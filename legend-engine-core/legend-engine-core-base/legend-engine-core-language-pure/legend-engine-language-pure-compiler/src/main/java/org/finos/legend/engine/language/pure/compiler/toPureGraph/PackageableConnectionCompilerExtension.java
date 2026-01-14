// Copyright 2024 Goldman Sachs
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package org.finos.legend.engine.language.pure.compiler.toPureGraph;

import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.api.list.MutableList;
import org.finos.legend.engine.language.pure.compiler.toPureGraph.extension.CompilerExtension;
import org.finos.legend.engine.language.pure.compiler.toPureGraph.extension.Processor;
import org.finos.legend.engine.protocol.pure.v1.model.packageableElement.connection.PackageableConnection;
import org.finos.legend.engine.protocol.pure.v1.model.packageableElement.mapping.Mapping;
import org.finos.legend.pure.m3.coreinstance.meta.core.runtime.Connection;
import org.finos.legend.pure.m3.coreinstance.meta.pure.runtime.PackageableConnection;
import org.finos.legend.pure.m3.coreinstance.RuntimeCoreInstanceFactoryRegistry;
import org.finos.legend.pure.m4.coreinstance.simple.SimpleCoreInstance;
import org.finos.legend.pure.m3.coreinstance.meta.pure.metamodel.PackageableElement;

public class PackageableConnectionCompilerExtension implements CompilerExtension
{
    @Override
    public MutableList<String> group()
    {
        return org.eclipse.collections.impl.factory.Lists.mutable.with("PackageableElement", "PackageableConnection");
    }

    @Override
    public CompilerExtension build()
    {
        return new PackageableConnectionCompilerExtension();
    }

    @Override
    public Iterable<? extends Processor<?>> getExtraProcessors()
    {
        return Lists.fixedSize.of(
                Processor.newProcessor(
                        PackageableConnection.class,
                        Lists.fixedSize.with(Mapping.class),
                        this::packageableConnectionFirstPass,
                        this::packageableConnectionSecondPass
                )
        );
    }

    private PackageableElement packageableConnectionFirstPass(PackageableConnection packageableConnection, CompileContext context)
    {
        org.finos.legend.pure.m3.coreinstance.meta.pure.runtime.PackageableConnection metamodel = (org.finos.legend.pure.m3.coreinstance.meta.pure.runtime.PackageableConnection) RuntimeCoreInstanceFactoryRegistry.REGISTRY.getFactory("meta::pure::runtime::PackageableConnection")
                .createCoreInstance(new SimpleCoreInstance(packageableConnection.name, SourceInformationHelper.toM3SourceInformation(packageableConnection.sourceInformation), context.pureModel.getClass("meta::pure::runtime::PackageableConnection")));
        Connection connection = packageableConnection.connectionValue.accept(new ConnectionFirstPassBuilder(context));
        return metamodel._connectionValue(connection);
    }

    private void packageableConnectionSecondPass(PackageableConnection packageableConnection, CompileContext context)
    {
        final Connection pureConnection = context.pureModel.getConnection(context.pureModel.buildPackageString(packageableConnection._package, packageableConnection.name), packageableConnection.sourceInformation);
        packageableConnection.connectionValue.accept(new ConnectionSecondPassBuilder(context, pureConnection));
    }
}
