from .. import package_mapper

from . import MayaCmd
from . import Arnold
from . import Generic
    
package_mapper.DeadlineToConductorPackageMapper.register(MayaCmd.MayaCmdMapper)
package_mapper.DeadlineToConductorPackageMapper.register(Arnold.ArnoldMapper)
package_mapper.DeadlineToConductorPackageMapper.register(Generic.GenericCmdMapper)
