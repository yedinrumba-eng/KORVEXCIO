frappe.pages["retail-owner-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Retail Owner Dashboard"), single_column: true });
	frappe.call({ method: "korvexcio.retail.dashboard.get_dashboard_data" }).then(({ message }) => {
		page.main.html(`<pre>${frappe.utils.escape_html(JSON.stringify(message, null, 2))}</pre>`);
	});
};
