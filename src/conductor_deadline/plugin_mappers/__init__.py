import conductor_deadline.package_mapper

import MayaCmd
import Arnold
    
conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.register(MayaCmd.MayaCmdMapper)
conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.register(Arnold.ArnoldMapper)