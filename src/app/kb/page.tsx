import { AppShell } from "@/components/app-shell";
import { KbSearch } from "@/components/kb-search";
import { KbUploader } from "@/components/kb-uploader";
import { SectionHeader } from "@/components/section-header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export default function KnowledgeBasePage() {
  return (
    <AppShell
      title="Knowledge Base"
      description="Upload, chunk, and retrieve sources with citations. Personal data stays segmented."
    >
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="glass-panel p-6">
          <SectionHeader
            title="Indexed Documents"
            description="Recently added documents across all personas."
          />
          <div className="mt-6 space-y-4">
            {["Pricing-Policy-2026.pdf", "HR-Handbook.md", "Client-QBR-Notes.txt"].map(
              (doc) => (
                <div key={doc} className="glass-card flex items-center justify-between p-4">
                  <div>
                    <div className="text-sm font-semibold">{doc}</div>
                    <div className="text-xs text-muted-foreground">
                      Indexed 30 minutes ago • 12 chunks
                    </div>
                  </div>
                  <Badge variant="outline">Work</Badge>
                </div>
              ),
            )}
          </div>
        </Card>
        <div className="space-y-6">
          <KbUploader />
          <KbSearch />
        </div>
      </div>
    </AppShell>
  );
}
