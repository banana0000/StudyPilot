from dash import dcc, html
import dash_mantine_components as dmc


def _metric(label, value_id, detail):
    return dmc.Card([
        dmc.Text(label, size="sm", c="dimmed", fw=600),
        dmc.Text("0", id=value_id, size="32px", fw=800, mt=6),
        dmc.Text(detail, size="xs", c="dimmed", mt=4),
    ], withBorder=True, radius="lg", padding="lg")


def _select(id_, label, data=None, value=None, **kwargs):
    return dmc.Select(id=id_, label=label, data=data or [], value=value, searchable=True, clearable=False, **kwargs)


def build_layout():
    return dmc.AppShell(
        header={"height": 72}, navbar={"width": 250, "breakpoint": "sm"}, padding="lg",
        children=[
            dmc.AppShellHeader(dmc.Group([
                dmc.Group([
                    dmc.ThemeIcon("BP", size=42, radius="md", variant="filled"),
                    dmc.Stack([dmc.Text("BusinessPilot AI", fw=800, size="lg"), dmc.Text("Business intelligence workspace", size="xs", c="dimmed")], gap=0),
                ], gap="sm"),
                dmc.Group([dmc.Text("Light", size="sm", c="dimmed"), dmc.Switch(id="dark-mode", **{"aria-label": "Switch color scheme"}), dmc.Text("Dark", size="sm", c="dimmed")], gap="xs"),
            ], justify="space-between", h="100%", px="lg")),
            dmc.AppShellNavbar([
                dmc.Stack([
                    dmc.NavLink(label="Dashboard", active=True, leftSection=dmc.ThemeIcon("D", size="sm", variant="light")),
                    dmc.NavLink(label="Document intelligence", leftSection=dmc.ThemeIcon("F", size="sm", variant="light")),
                    dmc.NavLink(label="AI workspace", leftSection=dmc.ThemeIcon("A", size="sm", variant="light")),
                ], gap=4, p="md"),
                dmc.Divider(),
                dmc.Card([dmc.Text("Ready to begin", fw=700, size="sm"), dmc.Text("Upload a document and ask BusinessPilot AI to analyze it.", size="xs", c="dimmed", mt=4)], withBorder=True, radius="md", m="md", p="sm"),
            ]),
            dmc.AppShellMain([
                dmc.LoadingOverlay(id="loading-overlay", visible=False, overlayProps={"blur": 2}),
                html.Div(id="notification-area", className="notification-area"),
                dmc.Stack([
                    dmc.Stack([dmc.Title("Business overview", order=1), dmc.Text("Upload business documents, find actions and risks, then turn insights into communication.", c="dimmed")], gap=4),
                    dmc.SimpleGrid([_metric("Documents", "metric-documents", "Files available this session"), _metric("Action items", "metric-actions", "Detected by AI analysis"), _metric("Deadlines", "metric-deadlines", "Detected by AI analysis")], cols={"base": 1, "sm": 3}, spacing="md"),
                    dmc.SimpleGrid([
                        dmc.Card([
                            dmc.Group([dmc.Title("Priority mix", order=3), dmc.Badge("Sample view", color="violet", variant="light")], justify="space-between"),
                            dmc.DonutChart(
                                data=[
                                    {"name": "High risk", "value": 22, "color": "red.6"},
                                    {"name": "Medium", "value": 35, "color": "orange.6"},
                                    {"name": "On track", "value": 43, "color": "teal.6"},
                                ],
                                chartLabel="100%", withTooltip=True, withLabels=True, thickness=22, mt="md",
                            ),
                        ], withBorder=True, radius="lg", padding="lg"),
                        dmc.Card([
                            dmc.Group([dmc.Title("Weekly activity", order=3), dmc.Badge("Sample view", color="cyan", variant="light")], justify="space-between"),
                            dmc.BarChart(
                                data=[
                                    {"day": "Mon", "Actions": 4, "Insights": 7}, {"day": "Tue", "Actions": 6, "Insights": 5},
                                    {"day": "Wed", "Actions": 3, "Insights": 8}, {"day": "Thu", "Actions": 7, "Insights": 6}, {"day": "Fri", "Actions": 5, "Insights": 9},
                                ],
                                dataKey="day", series=[{"name": "Actions", "color": "violet.6"}, {"name": "Insights", "color": "cyan.6"}],
                                withLegend=True, withTooltip=True, h=230, mt="md",
                            ),
                        ], withBorder=True, radius="lg", padding="lg"),
                    ], cols={"base": 1, "md": 2}, spacing="md"),                    dmc.Grid([
                        dmc.GridCol(dmc.Card([
                            dmc.Group([dmc.Title("Workspace readiness", order=3), dmc.Badge("Demo", color="teal", variant="light")], justify="space-between"),
                            dmc.Text("Complete these steps to turn a document into a decision-ready output.", size="sm", c="dimmed", mt="xs"),
                            dmc.Stack([
                                dmc.Group([dmc.Text("Document ingestion", size="sm", fw=600), dmc.Badge("Ready", color="teal", variant="light")], justify="space-between"),
                                dmc.Progress(value=100, color="teal", radius="xl"),
                                dmc.Group([dmc.Text("AI analysis", size="sm", fw=600), dmc.Badge("Local engine", color="yellow", variant="light")], justify="space-between"),
                                dmc.Progress(value=60, color="yellow", radius="xl"),
                                dmc.Group([dmc.Text("Report delivery", size="sm", fw=600), dmc.Badge("Available", color="violet", variant="light")], justify="space-between"),
                                dmc.Progress(value=85, color="violet", radius="xl"),
                            ], gap="xs", mt="md"),
                        ], withBorder=True, radius="lg", padding="lg"), span={"base": 12, "md": 5}),
                        dmc.GridCol(dmc.Card([
                            dmc.Title("Your workflow", order=3),
                            dmc.Timeline([
                                dmc.TimelineItem("Upload a PDF, DOCX, or TXT file", title="1. Add document", bullet=dmc.ThemeIcon("1", color="blue", variant="filled", size="sm")),
                                dmc.TimelineItem("Extract context, actions, deadlines, and risks", title="2. Analyze", bullet=dmc.ThemeIcon("2", color="violet", variant="filled", size="sm")),
                                dmc.TimelineItem("Create a chat answer, email, or executive report", title="3. Act", bullet=dmc.ThemeIcon("3", color="teal", variant="filled", size="sm")),
                            ], active=0, bulletSize=24, lineWidth=2, mt="md"),
                        ], withBorder=True, radius="lg", padding="lg"), span={"base": 12, "md": 7}),
                    ], gutter="md"),
                    dmc.Accordion([
                        dmc.AccordionItem([
                            dmc.AccordionControl(dmc.Group([dmc.Text("How does the AI document workflow work?", fw=600), dmc.Badge("Help", color="blue", variant="light")], justify="space-between")),
                            dmc.AccordionPanel("Upload a business document, select it in an AI workspace tab, then create an analysis, grounded chat answer, email, or report. All analysis and writing features run locally in this edition."),
                        ], value="workflow"),
                        dmc.AccordionItem([
                            dmc.AccordionControl("Privacy and session storage"),
                            dmc.AccordionPanel("Uploaded files are stored locally in the project data/uploads folder. Document metadata remains in the active browser session."),
                        ], value="privacy"),
                    ], variant="contained", radius="lg"),                    dmc.Tabs(value="documents", children=[
                        dmc.TabsList([
                            dmc.TabsTab("Documents", value="documents"), dmc.TabsTab("AI Analysis", value="analysis"), dmc.TabsTab("AI Chat", value="chat"), dmc.TabsTab("Email", value="email"), dmc.TabsTab("Report", value="report"),
                        ]),
                        dmc.TabsPanel(dmc.Grid([
                            dmc.GridCol(dmc.Card([
                                dmc.Title("Upload documents", order=3), dmc.Text("Supported: PDF, DOCX, TXT · 15 MB maximum per file", size="sm", c="dimmed", mt=4),
                                dcc.Upload(id="upload-documents", multiple=True, accept=".pdf,.docx,.txt", children=dmc.Button("Choose files", leftSection="+", mt="lg")),
                                html.Div(id="upload-feedback", style={"marginTop": "16px"}),
                            ], withBorder=True, radius="lg", padding="xl"), span={"base": 12, "md": 5}),
                            dmc.GridCol(dmc.Card([
                                dmc.Group([dmc.Title("Uploaded documents", order=3), dmc.Badge("Session files", variant="light")], justify="space-between"),
                                html.Div(id="document-list", style={"marginTop": "12px"}),
                            ], withBorder=True, radius="lg", padding="xl"), span={"base": 12, "md": 7}),
                        ], gutter="md"), value="documents", pt="lg"),
                        dmc.TabsPanel(dmc.Stack([
                            _select("analysis-document", "Document to analyze"),
                            dmc.Group([dmc.Button("Analyze document", id="analyze-button"), dmc.Button("Preview text", id="preview-button", variant="light")]),
                            dmc.Modal(id="document-preview", title="Document preview", size="xl", children=html.Pre(id="preview-content", style={"whiteSpace": "pre-wrap", "fontFamily": "inherit"})),
                            dmc.Card([dmc.Title("Executive summary", order=3), dmc.Text("Run an analysis to populate this section.", id="executive-summary", c="dimmed", mt="sm")], withBorder=True, radius="lg", padding="lg"),
                            dmc.SimpleGrid([
                                dmc.Card([dmc.Title("Key points", order=4), html.Div(id="key-points", className="analysis-list")], withBorder=True, radius="lg", padding="lg"),
                                dmc.Card([dmc.Title("Action items", order=4), html.Div(id="action-items", className="analysis-list")], withBorder=True, radius="lg", padding="lg"),
                                dmc.Card([dmc.Title("Deadlines", order=4), html.Div(id="deadlines", className="analysis-list")], withBorder=True, radius="lg", padding="lg"),
                                dmc.Card([dmc.Title("Risks", order=4), html.Div(id="risks", className="analysis-list")], withBorder=True, radius="lg", padding="lg"),
                            ], cols={"base": 1, "md": 2}),
                            dmc.Card([dmc.Title("Suggested next steps", order=4), html.Div(id="next-steps", className="analysis-list")], withBorder=True, radius="lg", padding="lg"),
                            dcc.Graph(id="analysis-chart", config={"displayModeBar": False}),
                        ], gap="md"), value="analysis", pt="lg"),
                        dmc.TabsPanel(dmc.Stack([
                            _select("chat-document", "Source document"),
                            dmc.Textarea(id="chat-question", label="Ask about this document", placeholder="What are the top three risks?", minRows=3),
                            dmc.Button("Ask BusinessPilot AI", id="chat-button", w="fit-content"),
                            dmc.Card([dmc.Text("Answer", fw=700), dmc.Text("Your AI answer will appear here.", id="chat-answer", c="dimmed", mt="sm", style={"whiteSpace": "pre-wrap"})], withBorder=True, radius="lg", padding="lg"),
                        ], gap="md"), value="chat", pt="lg"),
                        dmc.TabsPanel(dmc.Stack([
                            _select("email-document", "Source document"),
                            dmc.Grid([
                                dmc.GridCol(dmc.TextInput(id="email-recipient", label="Recipient", placeholder="e.g. Project stakeholders"), span={"base": 12, "sm": 4}),
                                dmc.GridCol(_select("email-purpose", "Purpose", ["Status update", "Follow-up", "Request approval", "Escalation"], "Status update"), span={"base": 12, "sm": 4}),
                                dmc.GridCol(_select("email-tone", "Tone", ["Professional", "Concise", "Friendly", "Urgent"], "Professional"), span={"base": 12, "sm": 4}),
                            ]),
                            dmc.Button("Generate email", id="email-button", w="fit-content"),
                            dmc.Textarea(id="email-output", label="Generated email", minRows=12),
                        ], gap="md"), value="email", pt="lg"),
                        dmc.TabsPanel(dmc.Stack([
                            _select("report-document", "Source document"),
                            dmc.Grid([
                                dmc.GridCol(_select("report-type", "Report type", ["Executive report", "Project update", "Risk report", "Meeting brief"], "Executive report"), span={"base": 12, "sm": 6}),
                                dmc.GridCol(dmc.Slider(id="report-detail", label="Detail level", min=1, max=10, value=5, marks=[{"value": 1, "label": "Brief"}, {"value": 10, "label": "Detailed"}]), span={"base": 12, "sm": 6}),
                            ]),
                            dmc.Button("Generate report", id="report-button", w="fit-content"),
                            dmc.Textarea(id="report-output", label="Generated report", minRows=16),
                        ], gap="md"), value="report", pt="lg"),
                    ]),
                ], gap="xl"),
            ], pos="relative"),
        ],
    )




