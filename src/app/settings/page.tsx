import { AppShell } from "@/components/app-shell";
import { SectionHeader } from "@/components/section-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

export default function SettingsPage() {
  return (
    <AppShell
      title="Settings"
      description="Persona tone, quiet hours, and domain defaults."
      actions={<Button className="rounded-full">Save</Button>}
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-panel p-6">
          <SectionHeader title="Persona Tone" description="Control style for each persona." />
          <div className="mt-6 space-y-4 text-sm">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Alex
              </div>
              <div className="mt-2 flex items-center gap-3">
                <span className="text-muted-foreground">Concise</span>
                <input type="range" min="0" max="100" className="w-full" />
                <span className="text-muted-foreground">Detailed</span>
              </div>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Sandra
              </div>
              <div className="mt-2 flex items-center gap-3">
                <span className="text-muted-foreground">Warm</span>
                <input type="range" min="0" max="100" className="w-full" />
                <span className="text-muted-foreground">Formal</span>
              </div>
            </div>
          </div>
        </Card>

        <Card className="glass-panel p-6">
          <SectionHeader title="Defaults" description="Domain and quiet hour controls." />
          <div className="mt-6 space-y-4 text-sm">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">Quiet Hours</div>
                <div className="text-xs text-muted-foreground">Auto-draft only during off-hours.</div>
              </div>
              <Switch />
            </div>
            <div>
              <div className="font-semibold">Default Domain</div>
              <Select>
                <SelectTrigger className="mt-2">
                  <SelectValue placeholder="Select domain" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="work">Work</SelectItem>
                  <SelectItem value="personal">Personal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <div className="font-semibold">Daily Briefing Time</div>
              <Input className="mt-2" type="time" defaultValue="08:00" />
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
