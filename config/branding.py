# Branding Configuration
# This file contains all branding and whitelabeling options for the application.
# Modify these values to customize the appearance and branding of your instance.

import os

class BrandingConfig:
    """
    Branding configuration class for whitelabeling the application.
    
    To customize your instance:
    1. Modify the values below
    2. Add your logo files to static/images/
    3. Optionally override CSS custom properties
    """
    
    # Application Identity
    APP_NAME = os.environ.get('APP_NAME', 'Nutgraf')
    APP_TAGLINE = os.environ.get('APP_TAGLINE', 'AI-Powered Article Summarization')
    APP_DESCRIPTION = os.environ.get('APP_DESCRIPTION', 'Transform lengthy articles into concise, actionable insights using advanced AI technology.')
    
    # Company/Organization Information
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Nutgraf')
    COMPANY_URL = os.environ.get('COMPANY_URL', 'https://nutgraf.ai')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@nutgraf.ai')
    
    # Visual Branding
    LOGO_URL = os.environ.get('LOGO_URL', '/static/images/logo.png')
    FAVICON_URL = os.environ.get('FAVICON_URL', '/static/images/favicon.ico')
    LOGO_ALT_TEXT = os.environ.get('LOGO_ALT_TEXT', f'{APP_NAME} Logo')
    
    # Color Scheme (CSS Custom Properties)
    THEME_COLORS = {
        'primary': os.environ.get('THEME_PRIMARY', '#3b82f6'),        # Main brand color
        'primary_hover': os.environ.get('THEME_PRIMARY_HOVER', '#2563eb'),  # Primary hover state
        'secondary': os.environ.get('THEME_SECONDARY', '#6b7280'),    # Secondary color
        'accent': os.environ.get('THEME_ACCENT', '#10b981'),          # Accent color (success, highlights)
        'background': os.environ.get('THEME_BACKGROUND', '#ffffff'),  # Main background
        'surface': os.environ.get('THEME_SURFACE', '#f9fafb'),       # Card/surface background
        'text_primary': os.environ.get('THEME_TEXT_PRIMARY', '#1f2937'),   # Primary text
        'text_secondary': os.environ.get('THEME_TEXT_SECONDARY', '#6b7280'), # Secondary text
        'border': os.environ.get('THEME_BORDER', '#e5e7eb'),         # Border color
        'error': os.environ.get('THEME_ERROR', '#dc2626'),           # Error color
        'warning': os.environ.get('THEME_WARNING', '#f59e0b'),       # Warning color
        'success': os.environ.get('THEME_SUCCESS', '#10b981'),       # Success color
    }
    
    # Navigation & UI Text
    UI_TEXT = {
        'nav_dashboard': os.environ.get('UI_NAV_DASHBOARD', 'Dashboard'),
        'nav_analyze': os.environ.get('UI_NAV_ANALYZE', 'Analyze'),
        'nav_saved_urls': os.environ.get('UI_NAV_SAVED_URLS', 'Saved URLs'),
        'nav_history': os.environ.get('UI_NAV_HISTORY', 'History'),
        'nav_settings': os.environ.get('UI_NAV_SETTINGS', 'Settings'),
        'nav_api_docs': os.environ.get('UI_NAV_API_DOCS', 'API Docs'),
        'nav_logout': os.environ.get('UI_NAV_LOGOUT', 'Logout'),
        
        'page_title_dashboard': os.environ.get('UI_PAGE_TITLE_DASHBOARD', 'Dashboard'),
        'page_title_analyze': os.environ.get('UI_PAGE_TITLE_ANALYZE', 'Analyze Articles'),
        'page_title_saved_urls': os.environ.get('UI_PAGE_TITLE_SAVED_URLS', 'Saved URLs'),
        'page_title_history': os.environ.get('UI_PAGE_TITLE_HISTORY', 'Summary History'),
        'page_title_settings': os.environ.get('UI_PAGE_TITLE_SETTINGS', 'Settings'),
        
        'footer_text': os.environ.get('UI_FOOTER_TEXT', f'© 2024 {COMPANY_NAME}. Built with Flask and AI.'),
    }
    
    # Feature Names & Descriptions
    FEATURE_TEXT = {
        'analyze_description': os.environ.get('FEATURE_ANALYZE_DESC', 'Input URLs and customize your summary preferences'),
        'saved_urls_description': os.environ.get('FEATURE_SAVED_URLS_DESC', 'Manage your saved URLs and analyze them when ready'),
        'history_description': os.environ.get('FEATURE_HISTORY_DESC', 'View and manage your previously generated summaries'),
        'dashboard_welcome': os.environ.get('FEATURE_DASHBOARD_WELCOME', f'Welcome to {APP_NAME}'),
        
        'export_csv_description': os.environ.get('FEATURE_EXPORT_CSV_DESC', f'Includes all data and summaries for re-importing into {APP_NAME}'),
        'export_bookmarks_description': os.environ.get('FEATURE_EXPORT_BOOKMARKS_DESC', 'Compatible with Chrome, Firefox, Safari, and other browsers'),
    }
    
    # API & Integration
    API_TEXT = {
        'api_name': os.environ.get('API_NAME', f'{APP_NAME} API'),
        'api_description': os.environ.get('API_DESCRIPTION', f'Programmatic access to {APP_NAME} summarization features'),
    }
    
    # Email & Communication
    EMAIL_SETTINGS = {
        'from_name': os.environ.get('EMAIL_FROM_NAME', APP_NAME),
        'from_email': os.environ.get('EMAIL_FROM_EMAIL', f'noreply@{COMPANY_NAME.lower()}.com'),
        'reply_to': os.environ.get('EMAIL_REPLY_TO', SUPPORT_EMAIL),
    }
    
    # Custom CSS Override
    CUSTOM_CSS_URL = os.environ.get('CUSTOM_CSS_URL', None)  # Optional custom CSS file
    
    # Analytics & Tracking (optional)
    ANALYTICS = {
        'google_analytics_id': os.environ.get('GOOGLE_ANALYTICS_ID', None),
        'hotjar_id': os.environ.get('HOTJAR_ID', None),
        'mixpanel_token': os.environ.get('MIXPANEL_TOKEN', None),
    }
    
    # Social & SEO
    SEO_META = {
        'og_title': os.environ.get('OG_TITLE', f'{APP_NAME} - {APP_TAGLINE}'),
        'og_description': os.environ.get('OG_DESCRIPTION', APP_DESCRIPTION),
        'og_image': os.environ.get('OG_IMAGE', '/static/images/og-image.png'),
        'twitter_handle': os.environ.get('TWITTER_HANDLE', None),
    }
    
    @classmethod
    def get_theme_css(cls):
        """Generate CSS custom properties for theming"""
        css_vars = []
        for key, value in cls.THEME_COLORS.items():
            css_var = f"--color-{key.replace('_', '-')}: {value};"
            css_vars.append(css_var)
        return '\n'.join(css_vars)
    
    @classmethod
    def to_dict(cls):
        """Convert configuration to dictionary for template use"""
        return {
            'app': {
                'name': cls.APP_NAME,
                'tagline': cls.APP_TAGLINE,
                'description': cls.APP_DESCRIPTION,
            },
            'company': {
                'name': cls.COMPANY_NAME,
                'url': cls.COMPANY_URL,
                'support_email': cls.SUPPORT_EMAIL,
            },
            'branding': {
                'logo_url': cls.LOGO_URL,
                'favicon_url': cls.FAVICON_URL,
                'logo_alt_text': cls.LOGO_ALT_TEXT,
                'custom_css_url': cls.CUSTOM_CSS_URL,
            },
            'colors': cls.THEME_COLORS,
            'ui': cls.UI_TEXT,
            'features': cls.FEATURE_TEXT,
            'api': cls.API_TEXT,
            'email': cls.EMAIL_SETTINGS,
            'analytics': cls.ANALYTICS,
            'seo': cls.SEO_META,
        }

# Create global instance
branding = BrandingConfig()