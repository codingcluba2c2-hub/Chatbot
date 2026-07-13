import os

os.makedirs('frontend/src/app/admin/tools', exist_ok=True)

with open('frontend/src/app/admin/tools/page.tsx', 'w') as f:
    f.write('''\
"use client";
import { GenericModule } from "@/components/admin/GenericModule";

export default function Page() {
  return (
    <div className="h-full">
      <GenericModule 
        title="Tool Registry" 
        endpoint="tools" 
        columns={[
          {key: "name", label: "Name", type: "text"}, 
          {key: "description", label: "Description", type: "text"}, 
          {key: "type", label: "Type", type: "text"}, 
          {key: "priority", label: "Priority", type: "number"}, 
          {key: "enabled", label: "Enabled", type: "boolean"}
        ]}
        defaultValues={{name: "", description: "", type: "generic", priority: 1, enabled: true}}
      />
    </div>
  );
}
''')

print("Created tools page")
