app_name = "korvexcio"
app_title = "KORVEXCIO"
app_publisher = "Korvex"
app_description = "ERP y POS multi-tenant con facturacion electronica (e-CF) para retail y food en Republica Dominicana"
app_email = "dev@korvexdev.cc"
app_license = "gpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "korvexcio",
# 		"logo": "/assets/korvexcio/logo.png",
# 		"title": "KORVEXCIO",
# 		"route": "/korvexcio",
# 		"has_permission": "korvexcio.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/korvexcio/css/korvexcio.css"
# app_include_js = "/assets/korvexcio/js/korvexcio.js"

# include js, css files in header of web template
# web_include_css = "/assets/korvexcio/css/korvexcio.css"
# web_include_js = "/assets/korvexcio/js/korvexcio.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "korvexcio/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "korvexcio/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "korvexcio.utils.jinja_methods",
# 	"filters": "korvexcio.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "korvexcio.install.before_install"
# after_install = "korvexcio.install.after_install"

# Migration
# ---------
# patron KSA (custom/*.json, no bench export-fixtures) — corre en cada
# bench migrate, no solo al instalar
after_migrate = [
    "korvexcio.custom_fields.sync_custom_fields",
    "korvexcio.roles.sync_roles",
]

# Uninstallation
# ------------

# before_uninstall = "korvexcio.uninstall.before_uninstall"
# after_uninstall = "korvexcio.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "korvexcio.utils.before_app_install"
# after_app_install = "korvexcio.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "korvexcio.utils.before_app_uninstall"
# after_app_uninstall = "korvexcio.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "korvexcio.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "korvexcio.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["korvexcio.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "*": {
        # S1.8 (D19) - equivalente al WITH CHECK de una politica RLS.
        # korvexcio.isolation.freeze_company filtra por doctype adentro,
        # asi que "*" es seguro: no hace nada en doctypes sin `company`.
        "validate": "korvexcio.isolation.freeze_company",
    },
    # S2.9 - Sales Invoice es de ERPNext, no se toca (regla 1). Todo entra
    # por aqui, nunca por override_doctype_class. El POS nunca espera a la
    # DGII para cerrar una venta: estos hooks son 100% locales, la llamada
    # real al proveedor la dispara la cola asincrona de S2.10.
    "Sales Invoice": {
        "validate": "korvexcio.ecf.sales_invoice_hooks.validate_rnc_threshold",
        "before_submit": "korvexcio.ecf.sales_invoice_hooks.reserve_encf",
        "on_submit": "korvexcio.ecf.sales_invoice_hooks.create_ecf_record",
        "before_cancel": "korvexcio.ecf.sales_invoice_hooks.block_cancel_if_accepted",
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"korvexcio.tasks.all"
# 	],
# 	"daily": [
# 		"korvexcio.tasks.daily"
# 	],
# 	"hourly": [
# 		"korvexcio.tasks.hourly"
# 	],
# 	"weekly": [
# 		"korvexcio.tasks.weekly"
# 	],
# 	"monthly": [
# 		"korvexcio.tasks.monthly"
# 	],
# }

# Testing
# -------

before_tests = "korvexcio.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "korvexcio.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "korvexcio.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "korvexcio.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["korvexcio.utils.before_request"]
# after_request = ["korvexcio.utils.after_request"]

# Job Events
# ----------
# before_job = ["korvexcio.utils.before_job"]
# after_job = ["korvexcio.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"korvexcio.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
