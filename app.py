import os

from dash import ALL, Dash, Input, Output, State, dcc, ctx
import dash_mantine_components as dmc
from services.document_service import save_upload, delete_upload, DocumentError
from ai.client import answer_question

app = Dash(__name__, title="StudyPilot")
server = app.server


def card(title, value, detail, color):
    return dmc.Card([
        dmc.Group([dmc.Text(title, size="sm", c="dimmed", fw=600), dmc.Badge("Today", color=color, variant="light")], justify="space-between"),
        dmc.Text(value, size="32px", fw=800, mt=8),
        dmc.Text(detail, size="xs", c="dimmed", mt=4),
    ], withBorder=True, radius="lg", padding="lg", className=f"metric-card metric-{color}")


def sentence_summary(text):
    sentences = [part.strip() for part in text.replace("\n", " ").split(".") if len(part.strip()) > 20]
    return ". ".join(sentences[:3]) + ("." if sentences else "No readable material yet.")


def build_quiz(text):
    sentences = [part.strip() for part in text.replace("\n", " ").split(".") if 25 <= len(part.strip()) <= 220][:3]
    quiz = []
    distractors = [
        "The material says this topic has no practical relevance.",
        "The material recommends skipping review and practice.",
        "The material states that no action or learning is required.",
    ]
    for index, sentence in enumerate(sentences):
        options = [sentence, distractors[index % 3], distractors[(index + 1) % 3]]
        options = options[index % 3:] + options[:index % 3]
        quiz.append({"question": "Which statement appears in the uploaded study material?", "options": options, "correct": sentence})
    return quiz


app.layout = dmc.MantineProvider(id="theme-provider", defaultColorScheme="light", children=[
    dcc.Store(id="material-store", storage_type="session", data={}),
    dcc.Store(id="quiz-store", storage_type="session", data=[]),
    dcc.Store(id="goals-store", storage_type="local", data=[]),
    dcc.Interval(id="focus-interval", interval=1000, n_intervals=0, disabled=True),    dmc.Modal(id="help-modal", opened=False, title="StudyPilot help", centered=True, children=dmc.Stack([
        dmc.Text("1. Upload a PDF, DOCX, or TXT file in Learning material."),
        dmc.Text("2. Read the extracted text in Material preview or ask a question about it."),
        dmc.Text("3. Use Focus session for a 25-minute study block, then check your knowledge with flashcards or quiz."),
        dmc.Text("4. Add small, clear goals and tick them off as you complete them."),
        dmc.Button("Close", id="close-help", color="blue", variant="light", w="fit-content"),
    ], gap="md")),
    dmc.AppShell(id="studypilot-shell",
        header={"height": 72}, navbar={"width": 250, "breakpoint": "sm"}, padding="lg",
        children=[
            dmc.AppShellHeader(dmc.Group([
                dmc.Group([
                    dmc.ThemeIcon("SP", size=42, radius="md", variant="filled", color="pink"),
                    dmc.Stack([dmc.Text("StudyPilot", fw=800, size="lg"), dmc.Text("Your focused learning workspace", size="xs", c="dimmed")], gap=0),
                ], gap="sm"),
                dmc.Tooltip(dmc.ColorSchemeToggle(id="color-scheme-toggle", lightIcon=chr(0x2600), darkIcon=chr(0x263E), variant="filled", color="pink", autoContrast=True, size="lg", **{"aria-label": "Toggle dark mode"}), label="Toggle dark mode"),
            ], justify="space-between", h="100%", px="lg")),
            dmc.AppShellNavbar([
                dmc.Stack([
                    dmc.NavLink(id="nav-summary", label="Summary", active=True, leftSection=dmc.ThemeIcon("S", size=32, radius="md", variant="filled", color="blue", autoContrast=True)),
                    dmc.NavLink(id="nav-material", label="Learning material", leftSection=dmc.ThemeIcon("M", size=32, radius="md", variant="filled", color="pink", autoContrast=True)),
                    dmc.NavLink(id="nav-focus", label="Focus session", leftSection=dmc.ThemeIcon("F", size=32, radius="md", variant="filled", color="blue", autoContrast=True)),
                    dmc.NavLink(id="nav-flashcard", label="Flashcards", leftSection=dmc.ThemeIcon("F", size=32, radius="md", variant="filled", color="pink", autoContrast=True)),
                    dmc.NavLink(id="nav-quiz", label="Knowledge check", leftSection=dmc.ThemeIcon("Q", size=32, radius="md", variant="filled", color="blue", autoContrast=True)),
                    dmc.NavLink(id="nav-goals", label="Learning goals", leftSection=dmc.ThemeIcon("G", size=32, radius="md", variant="filled", color="pink", autoContrast=True)),
                ], gap=4, p="md"),
                dmc.Divider(),
                dmc.Card([dmc.Text("Study tip", fw=700, size="sm"), dmc.Text("Work in one focused block, then take a short break.", size="xs", c="dimmed", mt=4)], withBorder=True, radius="md", m="md", p="sm"),
                dmc.Box(dmc.Button("Help", id="sidebar-help", leftSection="?", color="blue", variant="light", fullWidth=True), px="md", pb="md"),
            ]),
            dmc.AppShellMain(dmc.Stack([
                dmc.Stack([
                dmc.Stack([dmc.Title("Make learning visible", order=1), dmc.Text("Set goals, upload study material, and turn it into a focused practice session.", c="dimmed")], gap=4),
                dmc.SimpleGrid([
                    card("Focus time", "25 min", "Recommended study block", "pink"),
                    card("Learning goals", "0", "Keep your plan small", "blue"),
                    card("Material", "Ready", "Upload notes to begin", "blue"),
                ], id="metric-cards", cols={"base": 1, "sm": 3}, spacing="md"),
                dmc.SimpleGrid([
                    dmc.Card([
                        dmc.Group([dmc.Title("Study rhythm", order=3), dmc.Badge("Weekly", color="pink", variant="light")], justify="space-between"),
                        dmc.BarChart(
                            data=[{"day": "Mon", "minutes": 20}, {"day": "Tue", "minutes": 35}, {"day": "Wed", "minutes": 25}, {"day": "Thu", "minutes": 45}, {"day": "Fri", "minutes": 30}],
                            dataKey="day", series=[{"name": "minutes", "color": "pink.6"}], barProps={"radius": [10, 10, 0, 0]}, h=220, mt="md",
                        ),
                    ], withBorder=True, radius="lg", padding="lg"),
                    dmc.Card([
                        dmc.Group([dmc.Title("Learning balance", order=3), dmc.Badge("Today", color="blue", variant="light")], justify="space-between"),
                        dmc.DonutChart(data=[{"name": "Learn", "value": 50, "color": "pink.6"}, {"name": "Practice", "value": 30, "color": "blue.6"}, {"name": "Review", "value": 20, "color": "pink.4"}], chartLabel="100%", withLabels=True, withTooltip=True, thickness=24, mt="md"),
                    ], withBorder=True, radius="lg", padding="lg"),
                ], cols={"base": 1, "md": 2}, spacing="md"),
                ], id="summary-page"),
                dmc.Tabs(id="study-tabs", value="summary", children=[
                    dmc.TabsList([dmc.TabsTab("Summary", value="summary"), dmc.TabsTab("Material", value="material"), dmc.TabsTab("Focus", value="focus"), dmc.TabsTab("Flashcard", value="flashcard"), dmc.TabsTab("Quiz", value="quiz"), dmc.TabsTab("Goals", value="goals")]),                    dmc.TabsPanel(dmc.Grid([
                        dmc.GridCol(dmc.Card([
                            dmc.Title("Upload study material", order=3), dmc.Text("Use PDF, DOCX, or TXT notes. Processing happens locally.", c="dimmed", size="sm", mt=4),
                            dmc.Group([dcc.Upload(id="upload-material", multiple=False, accept=".pdf,.docx,.txt", children=dmc.Text("+ Choose study file", className="upload-link", fw=700, mt="lg")), dmc.Tooltip(dmc.ActionIcon(chr(0x1F5D1), id="clear-material", color="pink", variant="light", size="lg", mt="lg", **{"aria-label": "Remove material"}), label="Remove material")], gap="sm"),
                            dmc.Box(id="upload-feedback", mt="md"),
                        ], withBorder=True, radius="lg", padding="xl"), span={"base": 12, "md": 5}),
                        dmc.GridCol(dmc.Card([
                            dmc.Group([dmc.Title("Study material", order=3), dmc.Badge("Material", color="blue", variant="light")], justify="space-between"),
                            dmc.Text("Material preview", fw=700, size="sm", mt="md"),
                            dmc.Paper(dmc.ScrollArea(dmc.Text("The extracted document text will appear here after upload.", id="material-preview", size="sm", style={"whiteSpace": "pre-wrap"}), h=220, type="always", offsetScrollbars=True), withBorder=True, radius="md", p="sm", mt="xs"),
                            dmc.Divider(my="md"),
                            dmc.Textarea(id="question-input", label="Ask a question about this material", placeholder="What is the main idea?", minRows=3),
                            dmc.Button("Ask question", id="ask-question", color="blue", w="fit-content", mt="sm"),
                            dmc.Card([dmc.Text("Local answer", fw=700, size="sm"), dmc.Text("Upload material and ask a question.", id="question-answer", c="dimmed", mt="xs", style={"whiteSpace": "pre-wrap"})], withBorder=True, radius="md", padding="md", mt="sm"),
                        ], withBorder=True, radius="lg", padding="xl"), span={"base": 12, "md": 7}),
                    ], gutter="md"), value="material", pt="lg"),
                    dmc.TabsPanel(dmc.Card([
                        dmc.Group([dmc.Title("Focus timer", order=3), dmc.Badge("Pomodoro", color="blue", variant="light")], justify="space-between"),
                        dmc.Text("25:00", id="timer-display", size="48px", fw=800, ta="center", mt="lg"),
                        dmc.Progress(id="timer-progress", value=0, color="blue", radius="xl", mt="sm"),
                        dmc.Group([dmc.Button("Start", id="timer-start", color="blue"), dmc.Button("Pause", id="timer-pause", variant="light"), dmc.Button("Reset", id="timer-reset", variant="subtle")], justify="center", mt="lg"),
                        dmc.Alert("Tip: hide notifications and work on one small, well-defined outcome.", title="Protect your focus", color="blue", variant="light", mt="lg"),
                    ], withBorder=True, radius="lg", padding="xl"), value="focus", pt="lg"),
                    dmc.TabsPanel(dmc.Card([
                        dmc.Group([dmc.Title("Local flashcard", order=3), dmc.Badge("Review", color="pink", variant="light")], justify="space-between"),
                        dmc.Text("Upload study material to generate a study prompt.", id="flashcard-question", fw=700, mt="md"),
                        dmc.Accordion([dmc.AccordionItem([dmc.AccordionControl("Reveal answer"), dmc.AccordionPanel(dmc.Text("The answer will be generated from your uploaded material.", id="flashcard-answer"))], value="answer")], mt="md"),
                        dmc.SegmentedControl(data=[{"label": "Need review", "value": "review"}, {"label": "Almost", "value": "almost"}, {"label": "Know it", "value": "known"}], value="review", fullWidth=True, mt="lg"),
                    ], withBorder=True, radius="lg", padding="xl"), value="flashcard", pt="lg"),                    dmc.TabsPanel(dmc.Stack([
                        dmc.Group([dmc.Title("Quiz builder", order=3), dmc.Badge("Multiple choice", color="pink", variant="light")], justify="space-between"),
                        dmc.Text("Generate a short multiple-choice quiz from uploaded study material. Everything stays local.", c="dimmed", size="sm"),
                        dmc.Button("Generate quiz", id="generate-quiz", color="pink", w="fit-content"),
                        dmc.Box(id="quiz-content"),
                        dmc.Button("Check answers", id="grade-quiz", color="blue", w="fit-content"),
                        dmc.Box(id="quiz-feedback"),
                    ], gap="md"), value="quiz", pt="lg"),                    dmc.TabsPanel(dmc.Grid([
                        dmc.GridCol(dmc.Card([
                            dmc.TextInput(id="goal-input", label="New learning goal", placeholder="e.g. Review chapter 3"),
                            dmc.Button("Add goal", id="add-goal", color="pink", mt="md"),
                        ], withBorder=True, radius="lg", padding="lg"), span={"base": 12, "md": 5}),
                        dmc.GridCol(dmc.Card([dmc.Title("My goals", order=3), dmc.Box(id="goals-list", mt="xs")], withBorder=True, radius="lg", padding="lg"), span={"base": 12, "md": 7}),
                    ], gutter="md"), value="goals", pt="lg"),
                ]),
            ], gap="xl"), pos="relative"),
        ],
    ),
])


@app.callback(Output("help-modal", "opened"), Input("sidebar-help", "n_clicks"), Input("close-help", "n_clicks"), prevent_initial_call=True)
def toggle_help(*_):
    return ctx.triggered_id == "sidebar-help"

@app.callback(
    Output("study-tabs", "value"),
    Output("nav-summary", "active"),
    Output("nav-material", "active"),
    Output("nav-focus", "active"),
    Output("nav-flashcard", "active"),
    Output("nav-quiz", "active"),
    Output("nav-goals", "active"),
    Input("nav-summary", "n_clicks"),
    Input("nav-material", "n_clicks"),
    Input("nav-focus", "n_clicks"),
    Input("nav-flashcard", "n_clicks"),
    Input("nav-quiz", "n_clicks"),
    Input("nav-goals", "n_clicks"),
)
def navigate_sidebar(*_):
    tab = (ctx.triggered_id or "nav-summary").replace("nav-", "")
    return tab, *(tab == item for item in ("summary", "material", "focus", "flashcard", "quiz", "goals"))

@app.callback(Output("summary-page", "style"), Input("study-tabs", "value"))
def show_summary_page(tab):
    return {} if tab == "summary" else {"display": "none"}

@app.callback(Output("material-store", "data"), Output("upload-feedback", "children"), Input("upload-material", "contents"), Input("clear-material", "n_clicks"), State("upload-material", "filename"), State("material-store", "data"), prevent_initial_call=True)
def upload_material(content, _, filename, current_material):
    if ctx.triggered_id == "clear-material":
        deleted = delete_upload((current_material or {}).get("id"))
        message = "The local uploaded file was removed." if deleted else "There is no uploaded material to remove."
        return {}, dmc.Alert(message, title="Material removed", color="blue", variant="light")
    try:
        document = save_upload(content, filename)
        return document, dmc.Alert(f"{filename} is ready for study.", title="Material uploaded", color="blue", variant="light")
    except DocumentError as exc:
        return {}, dmc.Alert(str(exc), title="Upload failed", color="red", variant="light")


@app.callback(Output("flashcard-question", "children"), Output("flashcard-answer", "children"), Output("material-preview", "children"), Input("material-store", "data"))
def material_views(material):
    if not material:
        return "Upload study material to generate a study prompt.", "The answer will be generated from your uploaded material.", "The extracted document text will appear here after upload."
    text = material.get("text", "")
    summary = sentence_summary(text)
    return f"What is the central idea of {material.get('name', 'this material')}?", summary, text


@app.callback(Output("question-answer", "children"), Input("ask-question", "n_clicks"), State("question-input", "value"), State("material-store", "data"), prevent_initial_call=True)
def ask_question(_, question, material):
    if not material or not material.get("text"):
        return "Upload study material first."
    if not question or not question.strip():
        return "Type a question first."
    return answer_question(material.get("name", "material"), material["text"], question.strip())

@app.callback(Output("goals-store", "data"), Input("add-goal", "n_clicks"), State("goal-input", "value"), State("goals-store", "data"), prevent_initial_call=True)
def add_goal(_, goal, goals):
    goals = goals or []
    if goal and goal.strip():
        goals.append(goal.strip())
    return goals


@app.callback(Output("goals-list", "children"), Output("metric-cards", "children"), Input("goals-store", "data"))
def show_goals(goals):
    goals = goals or []
    items = dmc.Stack([dmc.Checkbox(label=goal, color="pink") for goal in goals], gap="xs") if goals else dmc.Text("Add your first learning goal.", c="dimmed", size="sm")
    return items, [card("Focus time", "25 min", "Recommended study block", "pink"), card("Learning goals", str(len(goals)), "Keep your plan small", "blue"), card("Material", "Ready", "Upload notes to begin", "blue")]


@app.callback(Output("focus-interval", "disabled"), Output("focus-interval", "n_intervals"), Input("timer-start", "n_clicks"), Input("timer-pause", "n_clicks"), Input("timer-reset", "n_clicks"), State("focus-interval", "n_intervals"), prevent_initial_call=True)
def control_timer(_, __, ___, ticks):
    trigger = ctx.triggered_id
    if trigger == "timer-start":
        return False, ticks
    if trigger == "timer-reset":
        return True, 0
    return True, ticks


@app.callback(Output("timer-display", "children"), Output("timer-progress", "value"), Input("focus-interval", "n_intervals"))
def display_timer(ticks):
    remaining = max(0, 25 * 60 - ticks)
    return f"{remaining // 60:02d}:{remaining % 60:02d}", round((ticks / (25 * 60)) * 100, 1)



@app.callback(Output("quiz-store", "data"), Output("quiz-feedback", "children"), Input("generate-quiz", "n_clicks"), State("material-store", "data"), prevent_initial_call=True)
def generate_quiz(_, material):
    if not material or not material.get("text"):
        return [], dmc.Alert("Upload study material before generating a quiz.", title="No material", color="pink", variant="light")
    quiz = build_quiz(material["text"])
    if not quiz:
        return [], dmc.Alert("The material needs a few longer sentences to create a quiz.", title="Not enough text", color="pink", variant="light")
    return quiz, dmc.Alert(f"Created {len(quiz)} questions from {material['name']}.", title="Quiz ready", color="pink", variant="light")


@app.callback(Output("quiz-content", "children"), Input("quiz-store", "data"))
def render_quiz(quiz):
    if not quiz:
        return dmc.Text("Upload material, then choose Generate quiz.", c="dimmed", size="sm")
    return dmc.Stack([
        dmc.Card([
            dmc.Text(f"Question {index + 1}", size="xs", c="dimmed", fw=700),
            dmc.Text(item["question"], fw=700, mt=4),
            dmc.RadioGroup([dmc.Radio(label=option, value=option, mt="xs") for option in item["options"]], id={"type": "quiz-answer", "index": index}, mt="sm"),
        ], withBorder=True, radius="lg", padding="lg")
        for index, item in enumerate(quiz)
    ], gap="md")


@app.callback(Output("quiz-feedback", "children", allow_duplicate=True), Input("grade-quiz", "n_clicks"), State({"type": "quiz-answer", "index": ALL}, "value"), State("quiz-store", "data"), prevent_initial_call=True)
def grade_quiz(_, answers, quiz):
    if not quiz:
        return dmc.Alert("Generate a quiz first.", title="No quiz", color="pink", variant="light")
    score = sum(answer == question["correct"] for answer, question in zip(answers, quiz))
    return dmc.Alert(f"Score: {score}/{len(quiz)}. Review any incorrect answer, then try again.", title="Quiz result", color="blue" if score == len(quiz) else "pink", variant="light")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)












