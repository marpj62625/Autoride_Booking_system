def generate_verification_email_html(otp: str, email: str = "") -> str:
    """Generates a professional, responsive HTML email template for email verification with official Autoride logo."""
    clean_otp = str(otp).strip()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Autoride Email Verification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #1f2937;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f3f4f6; padding: 40px 16px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 580px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.07); border: 1px solid #e5e7eb;">
          
          <!-- Green Header Banner with Official Branding -->
          <tr>
            <td style="background: linear-gradient(135deg, #00c853 0%, #00b14f 50%, #007a36 100%); padding: 36px 32px; text-align: center;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center">
                    <!-- Official Logo Badge -->
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto 14px auto;">
                      <tr>
                        <td align="center" valign="middle" style="background-color: #ffffff; width: 76px; height: 76px; border-radius: 50%; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.16); border: 2px solid rgba(255, 255, 255, 0.6); padding: 6px;">
                          <img src="https://autoride-booking-system.vercel.app/Autoride-logo-nobg.png" alt="Autoride Logo" width="62" height="62" style="display: block; width: 62px; height: 62px; object-fit: contain; margin: 0 auto; border: 0;" />
                        </td>
                      </tr>
                    </table>
                    <h1 style="margin: 0; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; text-transform: uppercase;">AUTORIDE</h1>
                    <p style="margin: 4px 0 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.9); font-weight: 500; letter-spacing: 0.5px;">Premium Car Rental &amp; Mobility Solutions</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Content Body -->
          <tr>
            <td style="padding: 36px 36px 28px 36px;">
              <h2 style="margin: 0 0 12px 0; font-size: 22px; font-weight: 800; color: #111827;">Verify Your Email Address</h2>
              <p style="margin: 0 0 18px 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                Thank you for creating an account with <strong>Autoride</strong>! To complete your registration and secure your profile, please enter the 6-digit verification code below:
              </p>

              <!-- OTP Code Display Box -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 28px 0;">
                <tr>
                  <td align="center" style="background: #f0fdf4; border: 2px dashed #00b14f; border-radius: 12px; padding: 24px 16px;">
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #15803d; letter-spacing: 1.5px; margin-bottom: 8px;">Verification Code</div>
                    <div style="font-family: 'Courier New', Courier, monospace, sans-serif; font-size: 42px; font-weight: 900; letter-spacing: 10px; color: #007a36; line-height: 1.2; margin: 4px 0;">
                      {clean_otp}
                    </div>
                    <div style="font-size: 12.5px; color: #6b7280; margin-top: 8px;">
                      ⏱️ Valid for <strong>10 minutes</strong> &bull; One-time use only
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Security Notice Callout -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #fefce8; border-left: 4px solid #eab308; border-radius: 6px; margin: 24px 0;">
                <tr>
                  <td style="padding: 14px 16px;">
                    <p style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; color: #854d0e;">
                      🛡️ Security Reminder
                    </p>
                    <p style="margin: 0; font-size: 12.5px; line-height: 1.5; color: #713f12;">
                      Never share this code with anyone. Autoride staff will never ask for your verification code via call, SMS, or chat.
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin: 20px 0 0 0; font-size: 13.5px; line-height: 1.5; color: #6b7280;">
                If you did not register for an account on Autoride, you can safely ignore this email. No changes will be made to your account.
              </p>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding: 0 36px;">
              <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 36px 36px 36px; text-align: center; background-color: #fafafa;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto 10px auto;">
                <tr>
                  <td align="center">
                    <img src="https://autoride-booking-system.vercel.app/Autoride-logo-nobg.png" alt="Autoride" width="38" height="38" style="display: block; width: 38px; height: 38px; object-fit: contain; margin: 0 auto; border: 0;" />
                  </td>
                </tr>
              </table>
              <p style="margin: 0 0 6px 0; font-size: 12.5px; font-weight: 700; color: #374151;">
                Autoride Car Rental Services
              </p>
              <p style="margin: 0 0 12px 0; font-size: 11.5px; color: #9ca3af; line-height: 1.5;">
                Fast, Safe, and Affordable Car Rentals Across the Region.<br>
                <a href="https://autoride-booking-system.vercel.app" target="_blank" style="color: #00b14f; text-decoration: none; font-weight: 600;">Visit Portal</a> &bull; 
                <a href="https://autoride-booking-system.vercel.app/#contact" target="_blank" style="color: #00b14f; text-decoration: none; font-weight: 600;">Help &amp; Support</a>
              </p>
              <p style="margin: 0; font-size: 11px; color: #9ca3af;">
                &copy; 2026 Autoride Company. All rights reserved.<br>
                This is an automated system email. Please do not reply directly to this message.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def generate_password_reset_email_html(temp_password: str, full_name: str = "", email: str = "") -> str:
    """Generates a professional, responsive HTML email template for password reset with official Autoride logo."""
    clean_pw = str(temp_password).strip()
    display_name = full_name or "Valued Customer"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Autoride Password Reset</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #1f2937;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f3f4f6; padding: 40px 16px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 580px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.07); border: 1px solid #e5e7eb;">
          
          <!-- Green Header Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #00c853 0%, #00b14f 50%, #007a36 100%); padding: 36px 32px; text-align: center;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center">
                    <!-- Official Logo Badge -->
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto 14px auto;">
                      <tr>
                        <td align="center" valign="middle" style="background-color: #ffffff; width: 76px; height: 76px; border-radius: 50%; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.16); border: 2px solid rgba(255, 255, 255, 0.6); padding: 6px;">
                          <img src="https://autoride-booking-system.vercel.app/Autoride-logo-nobg.png" alt="Autoride Logo" width="62" height="62" style="display: block; width: 62px; height: 62px; object-fit: contain; margin: 0 auto; border: 0;" />
                        </td>
                      </tr>
                    </table>
                    <h1 style="margin: 0; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; text-transform: uppercase;">AUTORIDE</h1>
                    <p style="margin: 4px 0 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.9); font-weight: 500; letter-spacing: 0.5px;">Account Security &amp; Recovery</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Content Body -->
          <tr>
            <td style="padding: 36px 36px 28px 36px;">
              <h2 style="margin: 0 0 12px 0; font-size: 22px; font-weight: 800; color: #111827;">Password Reset Request</h2>
              <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                Hello <strong>{display_name}</strong>,
              </p>
              <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                We received a request to reset your password for your Autoride account ({email}). Please use your temporary password below to sign in:
              </p>

              <!-- Temporary Password Card -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 24px 0;">
                <tr>
                  <td align="center" style="background: #f0fdf4; border: 2px dashed #00b14f; border-radius: 12px; padding: 22px 16px;">
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #15803d; letter-spacing: 1.5px; margin-bottom: 8px;">Temporary Password</div>
                    <div style="font-family: 'Courier New', Courier, monospace, sans-serif; font-size: 34px; font-weight: 900; letter-spacing: 4px; color: #007a36; line-height: 1.2;">
                      {clean_pw}
                    </div>
                  </td>
                </tr>
              </table>

              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #4b5563;">
                <strong>Next Step:</strong> Sign in with this temporary password and immediately go to <strong>Profile &gt; Security &gt; Change Password</strong> to create a new, permanent password.
              </p>

              <!-- Warning Callout -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 6px; margin: 24px 0;">
                <tr>
                  <td style="padding: 14px 16px;">
                    <p style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; color: #991b1b;">
                      ⚠️ Didn't request this change?
                    </p>
                    <p style="margin: 0; font-size: 12.5px; line-height: 1.5; color: #7f1d1d;">
                      If you did not request a password reset, please log in immediately to verify your account or contact our support team.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 36px 36px 36px; text-align: center; background-color: #fafafa; border-top: 1px solid #e5e7eb;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto 10px auto;">
                <tr>
                  <td align="center">
                    <img src="https://autoride-booking-system.vercel.app/Autoride-logo-nobg.png" alt="Autoride" width="38" height="38" style="display: block; width: 38px; height: 38px; object-fit: contain; margin: 0 auto; border: 0;" />
                  </td>
                </tr>
              </table>
              <p style="margin: 0 0 6px 0; font-size: 12.5px; font-weight: 700; color: #374151;">
                Autoride Car Rental Services
              </p>
              <p style="margin: 0 0 12px 0; font-size: 11.5px; color: #9ca3af;">
                <a href="https://autoride-booking-system.vercel.app" target="_blank" style="color: #00b14f; text-decoration: none; font-weight: 600;">Visit Portal</a> &bull; 
                <a href="https://autoride-booking-system.vercel.app/#login" target="_blank" style="color: #00b14f; text-decoration: none; font-weight: 600;">Sign In</a>
              </p>
              <p style="margin: 0; font-size: 11px; color: #9ca3af;">
                &copy; 2026 Autoride Company. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

if __name__ == '__main__':
    html_otp = generate_verification_email_html('224763', 'user@outlook.com')
    with open('scratch/preview_otp_email.html', 'w', encoding='utf-8') as f:
        f.write(html_otp)
    print("Preview generated successfully! Size:", len(html_otp))
