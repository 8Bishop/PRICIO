# Main PRICIO Application UI

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path

from core import Scraper, infer_intent
from utils import SearchCache, pick_best_price, calculate_price_stats, build_tip, init_history_file


class PRICIOApp(tk.Tk):
    # Main application window
    
    def __init__(self):
        super().__init__()
        self.title("PRICIO - Pricing Regional Intelligence Catalogue Insight Output")
        self.geometry("1320x780")
        self.minsize(1150, 680)
        
        # Data directory
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.data_dir / "price_history.csv"
        init_history_file(self.history_path)
        
        # Components
        self.cache = SearchCache()
        self.scraper = Scraper(logger=self.log)
        
        # State
        self._worker = None
        self.current_results = []
        self.current_keyword = ""
        self.current_intent = ""
        self.current_unit = "per unit"
        self.show_debug = tk.BooleanVar(value=False)
        
        # UI Setup
        self._setup_style()
        self._build_ui()
    
    def _setup_style(self):
        # Configure ttk styles
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10, "bold"))
    
    def _build_ui(self):
        # Build the user interface
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header
        self._build_header()
        
        # Main content area
        main = ttk.Frame(self, padding=(14, 8))
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)
        
        # Search controls
        self._build_search_controls(main)
        
        # Results table (left)
        self._build_results_table(main)
        
        # Right panel (summary, tips, quote)
        self._build_right_panel(main)
        
        # Status bar
        self._build_status_bar()
    
    def _build_header(self):
        # Build header section
        header = ttk.Frame(self, padding=(14, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        
        ttk.Label(header, text="PRICIO", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Pricing Regional Intelligence Catalogue Insight Output",
            foreground="#444",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
    
    def _build_search_controls(self, parent):
        # Build search control panel
        search = ttk.Labelframe(parent, text="Search (Direct Retailers)", padding=(12, 10))
        search.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        search.columnconfigure(1, weight=1)
        
        # Row 1: Main controls
        ttk.Label(search, text="Keyword:", style="SubHeader.TLabel").grid(row=0, column=0, sticky="w")
        self.keyword_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.keyword_var, width=44).grid(row=0, column=1, sticky="ew", padx=(8, 12))
        
        ttk.Label(search, text="Category:", style="SubHeader.TLabel").grid(row=0, column=2, sticky="w")
        self.category_var = tk.StringVar(value="Auto (Recommended)")
        ttk.Combobox(
            search,
            textvariable=self.category_var,
            state="readonly",
            width=22,
            values=["Auto (Recommended)", "Materials / Construction", "Electronics"],
        ).grid(row=0, column=3, sticky="w", padx=(8, 12))
        
        ttk.Label(search, text="Sort:", style="SubHeader.TLabel").grid(row=0, column=4, sticky="w")
        self.sort_var = tk.StringVar(value="Relevance (best match)")
        sort_combo = ttk.Combobox(
            search,
            textvariable=self.sort_var,
            state="readonly",
            width=22,
            values=[
                "Relevance (best match)",
                "Price: Low → High",
                "Price: High → Low",
            ],
        )
        sort_combo.grid(row=0, column=5, sticky="w", padx=(8, 12))
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.resort_current_results())
        
        self.mode_var = tk.StringVar(value="Online")
        ttk.Radiobutton(search, text="Online", variable=self.mode_var, value="Online").grid(row=0, column=6, padx=(6, 0))
        ttk.Radiobutton(search, text="Offline Demo", variable=self.mode_var, value="Offline Demo").grid(row=0, column=7, padx=(6, 0))
        
        ttk.Button(search, text="Search", command=self.on_search).grid(row=0, column=8, padx=(10, 6))
        ttk.Button(search, text="Stop", command=self.on_stop).grid(row=0, column=9)
        
        # Row 2: Debug toggle and tip
        ttk.Checkbutton(
            search, 
            text="Show Debug Log", 
            variable=self.show_debug,
            command=self.toggle_debug_log
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        
        ttk.Label(
            search,
            text="Hehe",
            foreground="#555",
        ).grid(row=1, column=2, columnspan=10, sticky="w", pady=(8, 0))
    
    def _build_results_table(self, parent):
        # Build results table
        left = ttk.Labelframe(parent, text="Results", padding=(10, 10))
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        
        cols = ("title", "store", "recommended", "price", "currency", "unit", "link")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=16)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        headings = {
            "title": ("Product Title", 360),
            "store": ("Supplier/Store", 150),
            "recommended": ("Rec.", 55),
            "price": ("Price", 85),
            "currency": ("Curr.", 55),
            "unit": ("Unit", 85),
            "link": ("Link", 520),
        }
        for key, (label, width) in headings.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")
        
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(left, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<Double-1>", self._on_row_open)
        
        # Debug log (hidden by default)
        self.debug_frame = ttk.Labelframe(left, text="Debug Log", padding=(10, 10))
        left.rowconfigure(2, weight=0, minsize=0)
        
        self.debug_log = scrolledtext.ScrolledText(self.debug_frame, height=8, wrap="word", font=("Courier", 9))
        self.debug_log.pack(fill="both", expand=True)
    
    def _build_right_panel(self, parent):
        # Build right panel with summary, tips, and quote
        right = ttk.Frame(parent)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        right.rowconfigure(3, weight=2)
        
        # Price summary
        self._build_price_summary(right)
        
        # Tip/Advisory
        self._build_tip_panel(right)
        
        # Quote/Cart
        self._build_quote_panel(right)
    
    def _build_price_summary(self, parent):
        # Build price summary panel
        summary = ttk.Labelframe(parent, text="Price Summary", padding=(12, 10))
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        summary.columnconfigure(1, weight=1)
        
        self.min_var = tk.StringVar(value="—")
        self.med_var = tk.StringVar(value="—")
        self.max_var = tk.StringVar(value="—")
        self.count_var = tk.StringVar(value="0")
        self.conf_var = tk.StringVar(value="—")
        
        def srow(label, var, r):
            ttk.Label(summary, text=label).grid(row=r, column=0, sticky="w")
            ttk.Label(summary, textvariable=var, font=("Segoe UI", 10, "bold")).grid(row=r, column=1, sticky="e")
        
        srow("Min:", self.min_var, 0)
        srow("Median:", self.med_var, 1)
        srow("Max:", self.max_var, 2)
        srow("# Valid Prices:", self.count_var, 3)
        srow("Confidence:", self.conf_var, 4)
    
    def _build_tip_panel(self, parent):
        # Build tip/advisory panel
        tip = ttk.Labelframe(parent, text="Tip / Advisory", padding=(12, 10))
        tip.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        tip.columnconfigure(0, weight=1)
        
        self.tip_text = tk.Text(tip, height=12, wrap="word")
        self.tip_text.grid(row=0, column=0, sticky="ew")
        self._set_tip("Tip will appear here after a successful search.")
    
    def _build_quote_panel(self, parent):
        # Build quote/cart panel
        quote = ttk.Labelframe(parent, text="Quote / Cart Preview", padding=(12, 10))
        quote.grid(row=3, column=0, sticky="nsew")
        quote.columnconfigure(0, weight=1)
        quote.rowconfigure(0, weight=1)
        
        self.quote_box = tk.Text(quote, wrap="word")
        self.quote_box.grid(row=0, column=0, sticky="nsew")
        qsb = ttk.Scrollbar(quote, orient="vertical", command=self.quote_box.yview)
        self.quote_box.configure(yscrollcommand=qsb.set)
        qsb.grid(row=0, column=1, sticky="ns")
        
        btn_row = ttk.Frame(quote)
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(btn_row, text="Add Selected", command=self.add_selected_to_quote).pack(side="left")
        ttk.Button(btn_row, text="Clear Quote", command=self.clear_quote).pack(side="left", padx=8)
    
    def _build_status_bar(self):
        # Build status bar
        status = ttk.Frame(self, padding=(14, 8))
        status.grid(row=2, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status, textvariable=self.status_var, foreground="#444").grid(row=0, column=0, sticky="w")
    

    # EVENT HANDLERS

    
    def on_search(self):
        # Handle search button click
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("Busy", "A search is already running. Click Stop to cancel it.")
            return
        
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showerror("Input Error", "Please enter a keyword.")
            return
        
        mode = self.mode_var.get()
        
        cat = self.category_var.get()
        if cat == "Materials / Construction":
            intent = "materials"
        elif cat == "Electronics":
            intent = "electronics"
        else:
            intent = infer_intent(keyword)
        
        sort_mode = self.sort_var.get()
        
        self.scraper.set_stop_flag(False)
        self.clear_results(keep_status=True)
        self.debug_log.delete("1.0", "end")
        
        self.status_var.set(f"Searching '{keyword}'…")
        self.log(f"=== Starting search for '{keyword}' ===")
        self.log(f"Category: {intent}")
        self.log(f"Sort: {sort_mode}")
        self.log("")
        
        self._worker = threading.Thread(
            target=self._search_worker,
            args=(keyword, mode, intent, sort_mode),
            daemon=True
        )
        self._worker.start()
    
    def on_stop(self):
        # Handle stop button click
        self.scraper.set_stop_flag(True)
        self.status_var.set("Stopping…")
    
    def toggle_debug_log(self):
        # Show/hide debug log
        if self.show_debug.get():
            self.debug_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
            self.tree.master.rowconfigure(2, weight=0, minsize=150)
        else:
            self.debug_frame.grid_forget()
            self.tree.master.rowconfigure(2, weight=0, minsize=0)
    
    def add_selected_to_quote(self):
        # Add selected items to quote
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item from the results table.")
            return
        
        for iid in selected:
            title, store, rec, price, currency, unit, link = self.tree.item(iid, "values")
            self.quote_box.insert(
                "end",
                f"- {title} | {store} {('(Recommended)' if rec == 'Yes' else '')}\n"
                f"  {currency} {price} ({unit})\n  {link}\n\n",
            )
        
        self.status_var.set(f"Added {len(selected)} item(s) to quote.")
    
    def clear_quote(self):
        # Clear quote/cart
        self.quote_box.delete("1.0", "end")
        self.status_var.set("Quote cleared.")
    
    def resort_current_results(self):
        # Re-sort current results when sort dropdown changes
        if not self.current_results:
            return
        
        sort_mode = self.sort_var.get()
        self._sort_results(self.current_results, self.current_keyword, sort_mode)
        
        self._display_results(self.current_results)
        
        best = pick_best_price(self.current_results)
        self._set_tip(build_tip(self.current_keyword, self.current_intent, sort_mode, best))
        
        self.status_var.set(f"Re-sorted by: {sort_mode}")
    
    def clear_results(self, keep_status=False):
        # Clear all results
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.min_var.set("—")
        self.med_var.set("—")
        self.max_var.set("—")
        self.count_var.set("0")
        self.conf_var.set("—")
        self._set_tip("Tip will appear here after a successful search.")
        if not keep_status:
            self.status_var.set("Results cleared.")
    
    def _on_row_open(self, _event):
        # Handle double-click on row - open in browser
        try:
            import webbrowser
            sel = self.tree.selection()
            if not sel:
                return
            link = self.tree.item(sel[0], "values")[6]
            if link:
                webbrowser.open(link)
        except Exception:
            pass
    

    # WORKER THREAD

    
    def _search_worker(self, keyword: str, mode: str, intent: str, sort_mode: str):
        # Background worker thread for searching
        try:
            if mode == "Offline Demo":
                results = self._fetch_demo(keyword, intent)
            else:
                # Check cache first
                cached = self.cache.get(keyword, intent)
                if cached:
                    self.log(f"📦 Using cached results ({len(cached)} items)")
                    results = cached
                else:
                    results = self.scraper.search_parallel(keyword, intent)
                    if results:
                        self.cache.set(keyword, intent, results)
            
            if self.scraper.stop_flag:
                self._ui(lambda: self.status_var.set("Stopped."))
                return
            
            if not results:
                self._ui(lambda: messagebox.showinfo("No Results", "No results found. Try a different keyword."))
                self._ui(lambda: self.status_var.set("No results."))
                self.log("❌ No results found from any retailer")
                return
            
            # Store results
            self.current_results = results
            self.current_keyword = keyword
            self.current_intent = intent
            self.current_unit = "per unit"
            
            # Sort
            self._sort_results(results, keyword, sort_mode)
            
            # Update UI
            def apply():
                self._display_results(results)
                stats = calculate_price_stats(results)
                self._update_summary(stats)
                
                best = pick_best_price(results)
                self._set_tip(build_tip(keyword, intent, sort_mode, best))
                
                self.status_var.set(f"Found {len(results)} results for '{keyword}' ({intent}).")
            
            self._ui(apply)
            self.log(f"\n✅ Total results: {len(results)}")
        
        except Exception as e:
            self._ui(lambda: messagebox.showwarning("Search Failed", str(e)))
            self._ui(lambda: self.status_var.set("Search failed."))
            self.log(f"❌ ERROR: {e}")
    
    # HELPER METHODS
    
    def _ui(self, fn):
        # Execute function on UI thread
        self.after(0, fn)
    
    def log(self, message):
        # Log message to debug log
        def _log():
            self.debug_log.insert("end", message + "\n")
            self.debug_log.see("end")
        self.after(0, _log)
    
    def _display_results(self, results):
        # Display results in tree view
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        
        for r in results:
            self.tree.insert(
                "", "end",
                values=(r["title"], r["store"], "Yes" if r["rec"] else "", 
                       r["price_disp"], r["cur"], "per unit", r["link"])
            )
    
    def _sort_results(self, results: list, keyword: str, sort_mode: str):
        # Sort results based on sort mode
        if sort_mode == "Relevance (best match)":
            results.sort(key=lambda r: (
                0 if r["rec"] else 1,
                -r.get("rel", 0.0),
                r["price"] if isinstance(r["price"], (int, float)) else 10**12
            ))
        elif sort_mode == "Price: Low → High":
            results.sort(key=lambda r: (
                0 if r["rec"] else 1,
                0 if isinstance(r["price"], (int, float)) else 1,
                r["price"] if isinstance(r["price"], (int, float)) else 10**12,
                -r.get("rel", 0.0),
            ))
        elif sort_mode == "Price: High → Low":
            results.sort(key=lambda r: (
                0 if r["rec"] else 1,
                0 if isinstance(r["price"], (int, float)) else 1,
                -(r["price"] if isinstance(r["price"], (int, float)) else -10**12),
                -r.get("rel", 0.0),
            ))
        else:
            results.sort(key=lambda r: (0 if r["rec"] else 1))
    
    def _update_summary(self, stats: dict):
        # Update price summary display
        if stats["count"] == 0:
            self.min_var.set("—")
            self.med_var.set("—")
            self.max_var.set("—")
            self.count_var.set("0")
            self.conf_var.set("—")
        else:
            self.min_var.set(f"{stats['min']:,.2f}")
            self.med_var.set(f"{stats['median']:,.2f}")
            self.max_var.set(f"{stats['max']:,.2f}")
            self.count_var.set(str(stats['count']))
            self.conf_var.set(stats['confidence'])
    
    def _set_tip(self, text):
        # Set tip/advisory text
        self.tip_text.configure(state="normal")
        self.tip_text.delete("1.0", "end")
        self.tip_text.insert("1.0", text)
        self.tip_text.configure(state="disabled")
    
    def _fetch_demo(self, keyword: str, intent: str) -> list:
        # Generate demo data for offline mode
        if intent == "materials":
            return [
                {"title": f"{keyword} - Wood Board 2m", "store": "acehardware.ph", "rec": True, 
                 "price": 500.0, "price_disp": "500.00", "cur": "PHP", "rel": 1.0, 
                 "link": "https://example.com/a"},
                {"title": f"{keyword} - Adhesive 250g", "store": "acehardware.ph", "rec": True, 
                 "price": 79.0, "price_disp": "79.00", "cur": "PHP", "rel": 0.8, 
                 "link": "https://example.com/b"},
            ]
        else:
            return [
                {"title": f"{keyword} - DDR4 16GB 3200MHz", "store": "pcx.com.ph", "rec": True, 
                 "price": 1999.0, "price_disp": "1,999.00", "cur": "PHP", "rel": 0.9, 
                 "link": "https://example.com/c"},
            ]
