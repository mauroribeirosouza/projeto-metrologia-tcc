from . import models
try:
	# optional packages: import if present
	from . import reports
except Exception:
	pass
try:
	from . import security
except Exception:
	pass
try:
	from . import data
except Exception:
	pass

# Version info
__version__ = '1.0.0'
__author__ = 'Mauro Ribeiro'
__license__ = 'LGPL-3'