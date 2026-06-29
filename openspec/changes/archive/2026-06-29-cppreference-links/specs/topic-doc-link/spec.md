## ADDED Requirements

### Requirement: doc_url field on TopicTemplate
`TopicTemplate` SHALL gain an optional `doc_url: str = ""` field. When non-empty, the
value SHALL be a fully-qualified HTTPS URL. When empty, no link widget is rendered.

#### Scenario: Topic with non-empty doc_url shows link button
- **WHEN** a `TopicTemplate` is constructed with `doc_url="https://en.cppreference.com/..."`
- **THEN** `topic.doc_url` returns the provided URL and `bool(topic.doc_url)` is `True`

#### Scenario: Topic with empty doc_url hides link button
- **WHEN** a `TopicTemplate` is constructed without specifying `doc_url`
- **THEN** `topic.doc_url` is `""` and no link button appears in the tab

### Requirement: Clickable documentation link in left column
Each topic tab whose `TopicTemplate.doc_url` is non-empty SHALL render a DPG button
labeled **"cppreference ↗"** in the left control column, immediately below the
explanation text and above the separator that precedes the controls. The button SHALL
use a distinct link-blue color (`(100, 180, 255, 255)`) to signal interactivity.
The button SHALL be enabled at all times, including while a compile/run action is in flight.

#### Scenario: Link button appears below explanation
- **WHEN** the topic tab is built and `doc_url` is non-empty
- **THEN** a button labeled "cppreference ↗" is visible in the left column below the explanation text

#### Scenario: Link button absent when doc_url is empty
- **WHEN** the topic tab is built and `doc_url` is empty
- **THEN** no link button is rendered in that position

### Requirement: Link opens in system browser
Clicking the documentation link button SHALL call `webbrowser.open(topic.doc_url)`,
opening the URL in the system default browser. The GUI SHALL remain responsive
during and after the browser open call (no blocking).

#### Scenario: Button click opens browser
- **WHEN** the user clicks the "cppreference ↗" button for any topic
- **THEN** the system default browser navigates to the topic's `doc_url`; the lab window stays open and responsive

#### Scenario: No import error from webbrowser
- **WHEN** `app_base.py` is imported
- **THEN** `import webbrowser` succeeds (stdlib, no installation required)
