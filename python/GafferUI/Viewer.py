##########################################################################
#
#  Copyright (c) 2011-2016, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import functools
import collections

import IECore

import Gaffer
import GafferUI

# import lazily to improve startup of apps which don't use GL functionality
IECoreGL = Gaffer.lazyImport( "IECoreGL" )

##########################################################################
# Viewer implementation
##########################################################################

## The Viewer provides the primary means of visualising the output
# of Nodes. It defers responsibility for the generation of content to
# the View classes, which are registered against specific types of
# Plug.
## \todo Support split screening two Views together and overlaying
# them etc. Hopefully we can support that entirely within the Viewer
# without modifying the Views themselves.
class Viewer( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( (
				GafferUI.GLWidget.BufferOptions.Depth,
				GafferUI.GLWidget.BufferOptions.Double,
				GafferUI.GLWidget.BufferOptions.AntiAlias )
			),
		)

		GafferUI.NodeSetEditor.__init__( self, self.__gadgetWidget, scriptNode, **kw )

		self.__nodeToolbars = []
		self.__viewToolbars = []
		self.__toolToolbars = []

		with GafferUI.ListContainer( borderWidth = 2, spacing = 0 ) as horizontalToolbars :

			# Top toolbars

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Vertical,
				parenting = {
					"verticalAlignment" : GafferUI.VerticalAlignment.Top,
				}
			) :

				for toolbarContainer in [ self.__viewToolbars, self.__nodeToolbars, self.__toolToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Top, self.getContext() ) )

			# Bottom toolbars

			with GafferUI.ListContainer(
				spacing = 0,
				orientation = GafferUI.ListContainer.Orientation.Vertical,
				parenting = {
					"verticalAlignment" : GafferUI.VerticalAlignment.Bottom,
				}
			) :

				for toolbarContainer in [ self.__toolToolbars, self.__nodeToolbars, self.__viewToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Bottom, self.getContext() ) )

		with GafferUI.ListContainer( borderWidth = 2, spacing = 0, orientation = GafferUI.ListContainer.Orientation.Horizontal ) as verticalToolbars :

			# Left toolbars

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Left,
					"verticalAlignment" : GafferUI.VerticalAlignment.Center,
				}
			) :

				self.__toolChooser = _ToolChooser()
				self.__primaryToolChangedConnection = self.__toolChooser.primaryToolChangedSignal().connect(
					Gaffer.WeakMethod( self.__primaryToolChanged )
				)

				for toolbarContainer in [ self.__viewToolbars, self.__nodeToolbars, self.__toolToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Left, self.getContext() ) )

			# Right toolbars

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Right,
					"verticalAlignment" : GafferUI.VerticalAlignment.Center,
				}
			) :

				for toolbarContainer in [ self.__toolToolbars, self.__nodeToolbars, self.__viewToolbars ] :
					toolbarContainer.append( _Toolbar( GafferUI.Edge.Right, self.getContext() ) )

		self.__gadgetWidget.addOverlay( horizontalToolbars )
		self.__gadgetWidget.addOverlay( verticalToolbars )

		self.__views = []
		# Indexed by view instance. We would prefer to simply
		# store tools as python attributes on the view instances
		# themselves, but we can't because that would create
		# circular references. Maybe it makes sense to be able to
		# query tools from a view anyway?
		self.__currentView = None

		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__contextMenuConnection = self.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ) )

		self._updateFromSet()

	def view( self ) :

		return self.__currentView

	def viewGadgetWidget( self ) :

		return self.__gadgetWidget

	__viewContextMenuSignal = Gaffer.Signal3()

	## Returns a signal emitted to generate a context menu for a view.
	# The signature for connected slots is `slot( viewer, view, menuDefiniton )`.
	# Slots should edit the menu definition in place.
	@classmethod
	def viewContextMenuSignal( cls ) :

		return cls.__viewContextMenuSignal

	def __repr__( self ) :

		return "GafferUI.Viewer( scriptNode )"

	def _updateFromSet( self ) :

		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__currentView = None

		node = self._lastAddedNode()
		if node :
			for plug in node.children( Gaffer.Plug ) :
				if plug.direction() == Gaffer.Plug.Direction.Out and not plug.getName().startswith( "__" ) :
					# try to reuse an existing view
					for view in self.__views :
						if view["in"].acceptsInput( plug ) :
							self.__currentView = view
							viewInput = self.__currentView["in"].getInput()
							if not viewInput or not viewInput.isSame( plug ) :
								self.__currentView["in"].setInput( plug )
							break # break out of view loop
					# if that failed then try to make a new one
					if self.__currentView is None :
						self.__currentView = GafferUI.View.create( plug )
						if self.__currentView is not None:
							Gaffer.NodeAlgo.applyUserDefaults( self.__currentView )
							self.__currentView.setContext( self.getContext() )
							self.__views.append( self.__currentView )
					# if we succeeded in getting a suitable view, then
					# don't bother checking the other plugs
					if self.__currentView is not None :
						break

		for toolbar in self.__nodeToolbars :
			toolbar.setNode( node )

		for toolbar in self.__viewToolbars :
			toolbar.setNode( self.__currentView )

		self.__toolChooser.setView( self.__currentView )

		if self.__currentView is not None :
			self.__gadgetWidget.setViewportGadget( self.__currentView.viewportGadget() )
		else :
			self.__gadgetWidget.setViewportGadget( GafferUI.ViewportGadget() )

		self.__primaryToolChanged()

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __primaryToolChanged( self, *unused ) :

		for toolbar in self.__toolToolbars :
			toolbar.setNode( self.__toolChooser.primaryTool() )

	def __keyPress( self, widget, event ) :

		if event.modifiers :
			return False

		for t in self.__toolChooser.tools() :
			if Gaffer.Metadata.nodeValue( t, "viewer:shortCut" ) == event.key :
				t["active"].setValue( True )
				return True

		return False

	def __contextMenu( self, widget ) :

		if self.view() is None :
			return False

		menuDefinition = IECore.MenuDefinition()
		self.viewContextMenuSignal()( self, self.view(), menuDefinition )

		if not len( menuDefinition.items() ) :
			return False

		self.__viewContextMenu = GafferUI.Menu( menuDefinition )
		self.__viewContextMenu.popup( self )

		return True

GafferUI.Editor.registerType( "Viewer", Viewer )

# Internal widget to simplify the management of node toolbars.
class _Toolbar( GafferUI.Frame ) :

	def __init__( self, edge, context, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None, **kw )

		# We store the 5 most recently used toolbars in a cache,
		# to avoid unnecessary reconstruction when switching back and
		# forth between the same set of nodes.
		self.__nodeToolbarCache = IECore.LRUCache( self.__cacheGetter, 5 )

		# Remove the SetMinAndMaxSize constraint that our base class added,
		# so that we expand to the full width of the viewport, and our toolbar
		# is centered inside.
		self._qtWidget().layout().setSizeConstraint( self._qtWidget().layout().SetDefaultConstraint )

		self.__edge = edge
		self.__context = context
		self.__node = []

	def setNode( self, node ) :

		if node == self.__node :
			return

		self.__node = node
		if self.__node is not None :
			toolbar = self.__nodeToolbarCache.get( ( self.__node, self.__edge ) )
			if toolbar is not None :
				toolbar.setContext( self.__context )
			self.setChild( toolbar )
		else :
			self.setChild( None )

		self.setVisible( self.getChild() is not None )

	def getNode( self ) :

		return self.__node

	@staticmethod
	def __cacheGetter( nodeAndEdge ) :

		return ( GafferUI.NodeToolbar.create( nodeAndEdge[0], nodeAndEdge[1] ), 1 )

# Internal widget to present the available tools for a view.
class _ToolChooser( GafferUI.Frame ) :

	class __ViewTools( object ) :

		def __init__( self, view ) :

			self.tools = [ GafferUI.Tool.create( n, view ) for n in GafferUI.Tool.registeredTools( view.typeId() ) ]
			self.tools.sort( key = lambda v : Gaffer.Metadata.nodeValue( v, "order" ) if Gaffer.Metadata.nodeValue( v, "order" ) is not None else 999 )

			self.__toolPlugSetConnections = [
				t.plugSetSignal().connect( Gaffer.WeakMethod( self.__toolPlugSet, fallbackResult = lambda plug : None ) ) for t in self.tools
			]
			self.__toolPlugDirtiedConnections = [
				t.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__toolPlugDirtied, fallbackResult = lambda plug : None ) ) for t in self.tools
			]

			with GafferUI.ListContainer( spacing = 1 ) as self.widgets :

				for tool in self.tools :

					toolTip = tool.getName()
					description = Gaffer.Metadata.nodeDescription( tool )
					if description :
						toolTip += "\n\n" + IECore.StringUtil.wrap( description, 80 )

					shortCut = Gaffer.Metadata.value( tool, "viewer:shortCut" )
					if shortCut is not None :
						toolTip += "\n\nShortcut : " + shortCut

					widget = GafferUI.BoolPlugValueWidget( tool["active"], toolTip = toolTip )

			GafferUI.WidgetAlgo.joinEdges( self.widgets )

			self.primaryTool = None
			self.primaryToolChangedSignal = Gaffer.Signal0()

			if len( self.tools ) :
				self.tools[0]["active"].setValue( True )

		def __toolPlugSet( self, plug ) :

			## \todo It feels like the View should probably own
			# the tools and do this work itself.

			tool = plug.node()
			if plug != tool["active"] :
				return

			if not plug.getValue() or Gaffer.Metadata.value( tool, "tool:exclusive" ) == False :
				return

			for t in self.tools :
				if not t.isSame( tool ) and Gaffer.Metadata.value( t, "tool:exclusive" ) != False :
					t["active"].setValue( False )

		def __toolPlugDirtied( self, plug ) :

			tool = plug.node()
			if plug != tool["active"] :
				return

			newPrimaryTool = self.primaryTool
			if plug.getValue() :
				newPrimaryTool = tool
			elif tool == self.primaryTool :
				newPrimaryTool = None

			if newPrimaryTool != self.primaryTool :
				self.primaryTool = newPrimaryTool
				self.primaryToolChangedSignal()

	def __init__( self, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None, **kw )

		self.__view = None
		self.__primaryToolChangedSignal = GafferUI.WidgetSignal()

		# Mapping from View to __ViewTools
		self.__viewTools = {}

	def tools( self ) :

		if self.__view is not None :
			return self.__viewTools[self.__view].tools
		else :
			return []

	def primaryTool( self ) :

		if self.__view is None :
			return None

		return self.__viewTools[self.__view].primaryTool

	def primaryToolChangedSignal( self ) :

		return self.__primaryToolChangedSignal

	def setView( self, view ) :

		if view == self.__view :
			return

		viewTools = self.__viewTools.get( view )
		if viewTools is None and view is not None :
			viewTools = self.__ViewTools( view )
			self.__viewTools[view] = viewTools

		self.setChild( viewTools.widgets if viewTools is not None else None )

		self.__primaryToolChangedConnection = None
		if viewTools is not None :
			self.__primaryToolChangedConnection = viewTools.primaryToolChangedSignal.connect(
				Gaffer.WeakMethod( self.__primaryToolChanged )
			)

		self.__view = view

	def getView( self ) :

		return self.__view

	def __primaryToolChanged( self ) :

		self.primaryToolChangedSignal()( self )
