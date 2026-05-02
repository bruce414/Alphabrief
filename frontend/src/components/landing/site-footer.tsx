export function SiteFooter() {
  return (
    <footer className="border-t border-border px-6 py-12">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold text-foreground">AlphaBrief</p>
          <p className="mt-1 text-sm text-muted-foreground">
            AI-powered financial briefings for investors. Early prototype.
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} AlphaBrief. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
