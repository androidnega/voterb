from django.db import models

# Operations Center uses existing models from other apps.
# This file is kept minimal as operations is a monitoring app.
# All data comes from:
# - accounts (User, Session, MFALog)
# - elections (Election)
# - voting (Vote)
# - notifications (DeliveryLog)
