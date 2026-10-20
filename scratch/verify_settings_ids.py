with open('admin_app/index.html', encoding='utf-8') as f:
    text = f.read()

required_ids = [
    'settingsAvatar', 'settingsName', 'settingsRole', 'settingsEmail',
    'superAdminProfileEditPill', 'superAdminEditProfileCard', 'adminChangePasswordCard',
    'superAdminPermissionsCard', 'pendingRequestsBadge',
    'adminDarkModeIcon', 'adminDarkModeLabel',
    'mobileSystemConfig', 'adminChatControlsConfigCard', 'mobileAddonsConfig',
    'mobileInsuranceConfig', 'mobileLocationsConfig', 'mobileBlackoutsConfig',
    'mobileSmtpConfig', 'smtpStatusLabel', 'mobileNewsletterConfig', 'nlSettingsSubtitle',
    'adminMaintenanceConfig',
    'lockPerm_system_config', 'lockPerm_chat_ai', 'lockPerm_addons', 'lockPerm_locations', 'lockPerm_blackout_dates'
]

missing = [el for el in required_ids if f'id="{el}"' not in text and f"id='{el}'" not in text]
if missing:
    print('FAILED! Missing IDs:', missing)
    exit(1)
else:
    print('SUCCESS: All required IDs are present in admin_app/index.html!')
