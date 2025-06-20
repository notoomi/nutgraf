# Whitelabeling Guide

This guide explains how to completely rebrand and whitelabel the Nutgraf application for your own use.

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your branding:**
   ```bash
   # Change the app name and description
   APP_NAME=YourBrand
   APP_TAGLINE=Your Custom Tagline
   APP_DESCRIPTION=Your custom description of the application
   
   # Update company information
   COMPANY_NAME=Your Company
   COMPANY_URL=https://yourcompany.com
   SUPPORT_EMAIL=support@yourcompany.com
   ```

3. **Add your visual assets:**
   - Place your logo at `static/images/logo.png`
   - Place your favicon at `static/images/favicon.ico`
   - Optionally add `static/images/og-image.png` for social sharing

4. **Restart the application** to see your changes.

## Comprehensive Customization

### 1. Application Identity

```bash
# Core application branding
APP_NAME=YourApp
APP_TAGLINE=Your Unique Value Proposition
APP_DESCRIPTION=Detailed description of what your app does

# Company information
COMPANY_NAME=Your Company Inc
COMPANY_URL=https://yourcompany.com
SUPPORT_EMAIL=support@yourcompany.com
```

### 2. Visual Branding

#### Logos and Icons
```bash
# Logo (displayed in navigation)
LOGO_URL=/static/images/your-logo.png
LOGO_ALT_TEXT=Your App Logo

# Favicon (browser tab icon)
FAVICON_URL=/static/images/your-favicon.ico
```

**Recommended sizes:**
- Logo: 200x50px (or maintain aspect ratio)
- Favicon: 32x32px or 16x16px

#### Color Scheme
Customize the entire color palette:
```bash
# Primary brand color (buttons, links, highlights)
THEME_PRIMARY=#your-brand-color
THEME_PRIMARY_HOVER=#darker-shade

# Supporting colors
THEME_SECONDARY=#6b7280
THEME_ACCENT=#10b981
THEME_BACKGROUND=#ffffff
THEME_SURFACE=#f9fafb
THEME_TEXT_PRIMARY=#1f2937
THEME_TEXT_SECONDARY=#6b7280
THEME_BORDER=#e5e7eb

# Status colors
THEME_ERROR=#dc2626
THEME_WARNING=#f59e0b
THEME_SUCCESS=#10b981
```

### 3. User Interface Text

#### Navigation
```bash
UI_NAV_DASHBOARD=Home
UI_NAV_ANALYZE=Process
UI_NAV_SAVED_URLS=Saved Items
UI_NAV_HISTORY=Archives
UI_NAV_SETTINGS=Configuration
UI_NAV_API_DOCS=Developer API
UI_NAV_LOGOUT=Sign Out
```

#### Page Titles
```bash
UI_PAGE_TITLE_DASHBOARD=Control Panel
UI_PAGE_TITLE_ANALYZE=Process Articles
UI_PAGE_TITLE_SAVED_URLS=Saved Content
UI_PAGE_TITLE_HISTORY=Content Archive
UI_PAGE_TITLE_SETTINGS=User Settings
```

#### Feature Descriptions
```bash
FEATURE_ANALYZE_DESC=Upload content and customize processing options
FEATURE_SAVED_URLS_DESC=Manage saved content and process when ready
FEATURE_HISTORY_DESC=Browse your processed content archive
FEATURE_DASHBOARD_WELCOME=Welcome to YourApp
FEATURE_EXPORT_CSV_DESC=Complete data export for backup and migration
FEATURE_EXPORT_BOOKMARKS_DESC=Browser-compatible bookmark format
```

#### Footer
```bash
UI_FOOTER_TEXT=© 2025 Notoomi
```

### 4. Advanced Customization

#### Custom CSS
For complete visual control, create a custom CSS file:

1. Create `static/css/custom-theme.css`
2. Set the environment variable:
   ```bash
   CUSTOM_CSS_URL=/static/css/custom-theme.css
   ```

Example custom CSS:
```css
/* Override specific components */
.navbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.btn-primary {
    background: linear-gradient(45deg, #your-color1, #your-color2);
    border: none;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

/* Custom fonts */
body {
    font-family: 'Your Custom Font', sans-serif;
}
```

#### Analytics Integration
```bash
# Google Analytics
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Hotjar (user behavior)
HOTJAR_ID=1234567

# Mixpanel (events)
MIXPANEL_TOKEN=your-token-here
```

#### SEO & Social Media
```bash
# Social sharing metadata
OG_TITLE=Your App - Your Tagline
OG_DESCRIPTION=Your comprehensive app description
OG_IMAGE=/static/images/your-social-image.png
TWITTER_HANDLE=yourbrand
```

### 5. Email Branding

```bash
# Email sender configuration
EMAIL_FROM_NAME=Your App
EMAIL_FROM_EMAIL=noreply@yourcompany.com
EMAIL_REPLY_TO=support@yourcompany.com
```

### 6. API Branding

```bash
# API documentation and references
API_NAME=Your App API
API_DESCRIPTION=Programmatic access to Your App features
```

## File Structure for Assets

```
static/
├── images/
│   ├── logo.png           # Main logo
│   ├── favicon.ico        # Browser icon
│   ├── og-image.png       # Social sharing image
│   └── your-assets/       # Additional images
├── css/
│   ├── main.css          # Core styles (don't modify)
│   └── custom-theme.css  # Your custom overrides
└── js/
    └── main.js           # Core JavaScript (don't modify)
```

## Environment Variables Reference

### Required for Basic Branding
- `APP_NAME` - Your application name
- `COMPANY_NAME` - Your company name
- `SUPPORT_EMAIL` - Support contact email

### Visual Branding
- `LOGO_URL` - Path to your logo
- `FAVICON_URL` - Path to your favicon
- `THEME_PRIMARY` - Primary brand color
- `THEME_PRIMARY_HOVER` - Primary color hover state

### Optional Enhancements
- `CUSTOM_CSS_URL` - Custom CSS file
- `GOOGLE_ANALYTICS_ID` - Analytics tracking
- `OG_IMAGE` - Social sharing image

## Examples

### Corporate Branding
```bash
APP_NAME=AcmeCorp Analytics
COMPANY_NAME=Acme Corporation
THEME_PRIMARY=#003366
THEME_SECONDARY=#666666
UI_FOOTER_TEXT=© 2024 Acme Corporation. Enterprise AI Solutions.
```

### Startup Branding
```bash
APP_NAME=QuickSumm
APP_TAGLINE=Lightning-fast article summaries
THEME_PRIMARY=#ff6b6b
THEME_ACCENT=#4ecdc4
FEATURE_DASHBOARD_WELCOME=Hey there! Ready to summarize?
```

### Academic Institution
```bash
APP_NAME=EduSummarize
COMPANY_NAME=University Research Institute
THEME_PRIMARY=#8b0000
FEATURE_ANALYZE_DESC=Analyze research papers and academic articles
```

## Implementation Details

### How Branding Works

The application uses a configuration-driven approach for whitelabeling:

1. **Environment Variables** → Read by `config/branding.py`
2. **BrandingConfig Class** → Processes and organizes settings
3. **Template Context** → Made available to all Jinja2 templates via `app.context_processor`
4. **CSS Custom Properties** → Dynamic theming through CSS variables

### Template Usage

In any template, access branding data through the `branding` object:

```html
<!-- Application name -->
<title>{{ branding.app.name }}</title>

<!-- Logo with alt text -->
<img src="{{ branding.branding.logo_url }}" 
     alt="{{ branding.branding.logo_alt_text }}">

<!-- Custom navigation text -->
<a href="/dashboard">{{ branding.ui.nav_dashboard }}</a>

<!-- Dynamic footer -->
<footer>{{ branding.ui.footer_text }}</footer>
```

### CSS Theming System

Colors are applied through CSS custom properties:

```css
/* These variables are auto-generated from your environment settings */
:root {
  --color-primary: #3b82f6;        /* From THEME_PRIMARY */
  --color-primary-hover: #2563eb;  /* From THEME_PRIMARY_HOVER */
  --color-secondary: #6b7280;      /* From THEME_SECONDARY */
  /* ... all other theme colors ... */
}

/* Use in your components */
.btn-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
}
```

### Adding New Brand Elements

To add custom branding elements:

1. **Add environment variable:**
   ```bash
   MY_CUSTOM_TEXT=Custom Value
   ```

2. **Update config/branding.py:**
   ```python
   # In the appropriate section
   CUSTOM_ELEMENT = os.environ.get('MY_CUSTOM_TEXT', 'Default Value')
   
   # Add to to_dict() method
   'custom': {
       'element': cls.CUSTOM_ELEMENT,
   }
   ```

3. **Use in templates:**
   ```html
   {{ branding.custom.element }}
   ```

## Testing Your Branding

### Development Testing
1. **Restart the application** after making changes
2. **Clear browser cache** to see updated assets
3. **Test all pages** to ensure consistency
4. **Check mobile responsiveness**
5. **Verify social sharing** with tools like Facebook Debugger

### Production Checklist
- [ ] All environment variables set correctly
- [ ] Logo files uploaded and accessible
- [ ] Favicon displays in browser tabs
- [ ] Colors render consistently across browsers
- [ ] Email branding works (test with password reset)
- [ ] API documentation reflects custom branding
- [ ] Social sharing images and metadata correct
- [ ] Custom CSS (if used) doesn't break responsive design

## Troubleshooting

### Images not showing
- Ensure files exist in `static/images/`
- Check file permissions
- Verify correct file extensions

### Colors not updating
- Restart the application
- Clear browser cache
- Check CSS syntax in custom files

### Text not changing
- Verify environment variable names
- Restart application after changes
- Check for typos in variable names

## Support

If you need help with whitelabeling, check:
1. This guide for common scenarios
2. The `.env.example` file for all available options
3. The `config/branding.py` file for advanced customization

Remember: Always backup your current configuration before making major changes!