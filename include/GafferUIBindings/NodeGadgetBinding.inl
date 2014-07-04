//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUIBINDINGS_NODEGADGETBINDING_INL
#define GAFFERUIBINDINGS_NODEGADGETBINDING_INL

namespace GafferUIBindings
{

namespace Detail
{

template<typename T>
GafferUI::NodulePtr nodule( T &p, Gaffer::ConstPlugPtr plug )
{
	return p.T::nodule( plug );
}

template<typename T>
Imath::V3f noduleTangent( T &p, const GafferUI::Nodule *nodule )
{
	return p.T::noduleTangent( nodule );
}

} // namespace Detail

template<typename T, typename TWrapper>
NodeGadgetClass<T, TWrapper>::NodeGadgetClass( const char *docString )
	:	GadgetClass<T, TWrapper>( docString )
{
	def( "nodule", &Detail::nodule<T> );
	def( "noduleTangent", &Detail::noduleTangent<T> );
}

} // namespace GafferUIBindings

#endif // GAFFERUIBINDINGS_NODEGADGETBINDING_INL