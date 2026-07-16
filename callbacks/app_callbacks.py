from dash import Input, Output, State, html, no_update
import dash_mantine_components as dmc
import plotly.graph_objects as go
from ai.client import AIServiceError, analyze_document, answer_question, generate_email, generate_report
from services.document_service import DocumentError, save_upload


def _find(documents, document_id):
    return next((doc for doc in (documents or []) if doc["id"] == document_id), None)


def _items(values, formatter=lambda value: value):
    if not values:
        return dmc.Text("No items identified.", c="dimmed", size="sm")
    return dmc.List([dmc.ListItem(formatter(value)) for value in values], spacing="xs", size="sm")


def _analysis_blank(message="Run an analysis to populate this section."):
    return message, _items([]), _items([]), _items([]), _items([]), _items([]), go.Figure()


def register_callbacks(app):
    @app.callback(Output("theme-provider", "forceColorScheme"), Output("theme-store", "data"), Input("dark-mode", "checked"))
    def set_theme(is_dark):
        theme = "dark" if is_dark else "light"
        return theme, theme

    @app.callback(Output("documents-store", "data"), Output("upload-feedback", "children"), Input("upload-documents", "contents"), State("upload-documents", "filename"), State("documents-store", "data"), prevent_initial_call=True)
    def upload_documents(contents, filenames, existing):
        documents = existing or []
        accepted, errors = [], []
        for content, filename in zip(contents or [], filenames or []):
            try:
                accepted.append(save_upload(content, filename))
            except DocumentError as exc:
                errors.append(f"{filename}: {exc}")
        documents.extend(accepted)
        message = f"Added {len(accepted)} document(s)."
        if errors:
            message += " " + " ".join(errors)
        color = "green" if accepted else "red"
        return documents, dmc.Alert(message, title="Upload complete" if accepted else "Upload failed", color=color, variant="light")

    @app.callback(
        Output("analysis-document", "data"), Output("analysis-document", "value"),
        Output("chat-document", "data"), Output("chat-document", "value"),
        Output("email-document", "data"), Output("email-document", "value"),
        Output("report-document", "data"), Output("report-document", "value"),
        Output("document-list", "children"), Output("metric-documents", "children"),
        Input("documents-store", "data"),
    )
    def render_documents(documents):
        data = [{"value": doc["id"], "label": doc["name"]} for doc in (documents or [])]
        value = data[0]["value"] if data else None
        if not documents:
            listing = dmc.Text("No documents uploaded yet.", c="dimmed", size="sm")
        else:
            listing = dmc.Stack([
                dmc.Group([dmc.Group([dmc.ThemeIcon(doc["extension"].upper(), variant="light", size="sm"), dmc.Text(doc["name"], fw=600, size="sm")], gap="sm"), dmc.Text(f'{doc["size_kb"]} KB', c="dimmed", size="xs")], justify="space-between")
                for doc in documents
            ], gap="xs")
        return data, value, data, value, data, value, data, value, listing, str(len(documents or []))

    @app.callback(
        Output("analysis-store", "data"), Output("executive-summary", "children"), Output("key-points", "children"), Output("action-items", "children"), Output("deadlines", "children"), Output("risks", "children"), Output("next-steps", "children"), Output("analysis-chart", "figure"),
        Input("analyze-button", "n_clicks"), State("analysis-document", "value"), State("documents-store", "data"), prevent_initial_call=True,
    )
    def analyze(_, document_id, documents):
        doc = _find(documents, document_id)
        if not doc:
            blank = _analysis_blank("Choose a document before analyzing.")
            return {}, *blank
        try:
            analysis = analyze_document(doc["name"], doc["text"])
            action_items = analysis.get("action_items", [])
            deadlines = analysis.get("deadlines", [])
            risks = analysis.get("risks", [])
            figure = go.Figure(go.Bar(
                x=["Key points", "Actions", "Deadlines", "Risks", "Next steps"],
                y=[len(analysis.get("key_points", [])), len(action_items), len(deadlines), len(risks), len(analysis.get("suggested_next_steps", []))],
                marker_color=["#7c3aed", "#2563eb", "#06b6d4", "#f59e0b", "#ef4444"],
            ))
            figure.update_layout(title="Colorful analysis overview", template="plotly_white", height=300, margin=dict(l=20, r=20, t=50, b=20))
            return analysis, analysis.get("executive_summary", "No summary returned."), _items(analysis.get("key_points", [])), _items(action_items, lambda item: f'{item.get("task", "Action")} — {item.get("owner", "Owner not specified")} ({item.get("priority", "Priority not specified")})'), _items(deadlines, lambda item: f'{item.get("date", "Date not specified")}: {item.get("item", "Deadline") }'), _items(risks, lambda item: f'{item.get("risk", "Risk")} ({item.get("severity", "Severity not specified")})'), _items(analysis.get("suggested_next_steps", [])), figure
        except AIServiceError as exc:
            blank = _analysis_blank(f"Analysis unavailable: {exc}")
            return {}, *blank

    @app.callback(Output("metric-actions", "children"), Output("metric-deadlines", "children"), Input("analysis-store", "data"))
    def update_metrics(analysis):
        analysis = analysis or {}
        return str(len(analysis.get("action_items", []))), str(len(analysis.get("deadlines", [])))

    @app.callback(Output("document-preview", "opened"), Output("preview-content", "children"), Input("preview-button", "n_clicks"), State("analysis-document", "value"), State("documents-store", "data"), prevent_initial_call=True)
    def preview(_, document_id, documents):
        doc = _find(documents, document_id)
        return True, doc["text"][:12000] if doc else "Choose a document first."

    @app.callback(Output("chat-answer", "children"), Input("chat-button", "n_clicks"), State("chat-document", "value"), State("chat-question", "value"), State("documents-store", "data"), prevent_initial_call=True)
    def chat(_, document_id, question, documents):
        doc = _find(documents, document_id)
        if not doc or not question:
            return "Choose a document and enter a question."
        try:
            return answer_question(doc["name"], doc["text"], question)
        except AIServiceError as exc:
            return f"AI chat unavailable: {exc}"

    @app.callback(Output("email-output", "value"), Input("email-button", "n_clicks"), State("email-document", "value"), State("email-purpose", "value"), State("email-tone", "value"), State("email-recipient", "value"), State("documents-store", "data"), prevent_initial_call=True)
    def email(_, document_id, purpose, tone, recipient, documents):
        doc = _find(documents, document_id)
        if not doc:
            return "Choose a source document first."
        try:
            return generate_email(doc["name"], doc["text"], purpose, tone, recipient)
        except AIServiceError as exc:
            return f"Email generation unavailable: {exc}"

    @app.callback(Output("report-output", "value"), Input("report-button", "n_clicks"), State("report-document", "value"), State("report-type", "value"), State("report-detail", "value"), State("documents-store", "data"), prevent_initial_call=True)
    def report(_, document_id, report_type, detail, documents):
        doc = _find(documents, document_id)
        if not doc:
            return "Choose a source document first."
        try:
            return generate_report(doc["name"], doc["text"], report_type, detail)
        except AIServiceError as exc:
            return f"Report generation unavailable: {exc}"

