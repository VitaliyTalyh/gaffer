//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "boost/python.hpp"

#include "IECorePython/RefCountedBinding.h"

#include "Gaffer/Plug.h"
#include "Gaffer/PlugAlgo.h"

#include "PlugAlgoBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;

void GafferModule::bindPlugAlgo()
{
	object module( borrowed( PyImport_AddModule( "Gaffer.PlugAlgo" ) ) );
	scope().attr( "PlugAlgo" ) = module;
	scope moduleScope( module );

	def( "replacePlug", &PlugAlgo::replacePlug, ( arg( "parent" ), arg( "plug" ) ) );

	def( "canPromote", &PlugAlgo::canPromote, ( arg( "plug" ), arg( "parent" ) = object() ) );
	def( "promote", &PlugAlgo::promote, ( arg( "plug" ), arg( "parent" ) = object(), arg( "excludeMetadata" ) = "layout:*" ), return_value_policy<CastToIntrusivePtr>() );
	def( "promoteWithName", &PlugAlgo::promoteWithName, ( arg( "plug" ), arg( "name" ), arg( "parent" ) = object(), arg( "excludeMetadata" ) = "layout:*" ), return_value_policy<CastToIntrusivePtr>() );
	def( "isPromoted", &PlugAlgo::isPromoted, ( arg( "plug" ) ) );
	def( "unpromote", &PlugAlgo::unpromote, ( arg( "plug" ) ) );

}
