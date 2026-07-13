import os
import textwrap

pages = [
    ('greetings', 'Greetings', 'greetings', '[{key: "greeting_text", label: "Text", type: "text"}, {key: "intent", label: "Intent", type: "text"}, {key: "priority", label: "Priority", type: "number"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{greeting_text: "", intent: "Greeting", priority: 1, enabled: true}'),
    ('farewells', 'Farewells', 'farewells', '[{key: "farewell_text", label: "Text", type: "text"}, {key: "intent", label: "Intent", type: "text"}, {key: "priority", label: "Priority", type: "number"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{farewell_text: "", intent: "Farewell", priority: 1, enabled: true}'),
    ('faqs', 'FAQs', 'faqs', '[{key: "question", label: "Question", type: "text"}, {key: "answer", label: "Answer", type: "text"}, {key: "aliases", label: "Aliases", type: "list"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{question: "", answer: "", aliases: [], enabled: true}'),
    ('fastpaths', 'FastPaths', 'fastpaths', '[{key: "trigger", label: "Trigger", type: "text"}, {key: "response", label: "Response", type: "text"}, {key: "aliases", label: "Aliases", type: "list"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{trigger: "", response: "", aliases: [], enabled: true}'),
    ('aliases', 'Aliases', 'aliases', '[{key: "shortcut", label: "Shortcut", type: "text"}, {key: "expansion", label: "Expansion", type: "text"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{shortcut: "", expansion: "", enabled: true}'),
    ('regex', 'Regex Rules', 'regex_rules', '[{key: "name", label: "Name", type: "text"}, {key: "pattern", label: "Pattern", type: "text"}, {key: "description", label: "Description", type: "text"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{name: "", pattern: "", description: "", enabled: true}'),
    ('intents', 'Intent Mapping', 'intents', '[{key: "name", label: "Name", type: "text"}, {key: "description", label: "Description", type: "text"}, {key: "priority", label: "Priority", type: "number"}, {key: "enabled", label: "Enabled", type: "boolean"}]', '{name: "", description: "", priority: 1, enabled: true}')
]

template = textwrap.dedent('''\
    "use client";
    import { GenericModule } from "@/components/admin/GenericModule";
    
    export default function Page() {
      return (
        <div className="h-full">
          <GenericModule 
            title="<<TITLE>>" 
            endpoint="<<ENDPOINT>>" 
            columns={<<COLUMNS>>}
            defaultValues={<<DEFAULTS>>}
          />
        </div>
      );
    }
''')

for folder, title, endpoint, columns, defaults in pages:
    path = f'frontend/src/app/admin/{folder}/page.tsx'
    with open(path, 'w') as f:
        content = template.replace('<<TITLE>>', title).replace('<<ENDPOINT>>', endpoint).replace('<<COLUMNS>>', columns).replace('<<DEFAULTS>>', defaults)
        f.write(content)
