const BACKEND_URL = "http://127.0.0.1:8000";

function sqlAgent() {
    return {
        // UI State
        query: "",
        selectedDb: "hr",
        loading: false,
        results: [],
        pendingOperations: [],
        dbStats: null,
        conversationHistory: [],
        systemStats: { totalQueries: 0, pendingCount: 0 },
        systemMessage: "",
        pendingDetails: null,

        // --- MAIN QUERY EXECUTION ---
        async executeQuery() {
            if (!this.query.trim()) return;
            this.loading = true;
            this.systemMessage = "";
            try {
                const res = await fetch(BACKEND_URL + "/nl-query", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: this.query,
                        target_db: this.selectedDb
                    })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Query failed");
                this.results.unshift(data);
                this.conversationHistory.push({
                    query: this.query,
                    result: data,
                    timestamp: Date.now()
                });
                // Update stats
                this.systemStats.totalQueries++;
                if (data.execution_status === "requires_human_approval") {
                    this.systemStats.pendingCount++;
                    this.refreshPending();
                }
            } catch (e) {
                this.results.unshift({
                    query: this.query,
                    error: e.message,
                    status: "error"
                });
                this.systemMessage = e.message;
            } finally {
                this.loading = false;
            }
        },

        // --- CLEAR RESULTS ---
        clearResults() {
            this.results = [];
            this.systemMessage = "";
        },

        // --- PENDING OPERATIONS ---
        async refreshPending() {
            try {
                const res = await fetch(BACKEND_URL + "/pending");
                const data = await res.json();
                this.pendingOperations = data.pending || [];
                this.systemStats.pendingCount = this.pendingOperations.filter(p => p.status === "PENDING").length;
            } catch (e) {
                this.systemMessage = "Failed to load pending operations";
            }
        },

        async approvePending(id) {
            try {
                this.systemMessage = "Approving operation...";
                const res = await fetch(BACKEND_URL + `/confirm`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pending_id: id, approve: true })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Approval failed");
                this.systemMessage = "Operation approved and executed.";
                this.refreshPending();
                // Update the corresponding result in results
                this.results = this.results.map(r => {
                    if (r.pending_id === id) {
                        return {
                            ...r,
                            execution_status: "executed_directly",
                            message: "This request has been approved and executed.",
                            pending_id: null // Remove pending_id so the yellow box disappears
                        };
                    }
                    return r;
                });
                // Optionally close modal if open
                if (this.pendingDetails && this.pendingDetails.id === id) {
                    this.pendingDetails = null;
                }
            } catch (e) {
                this.systemMessage = e.message || "Approval failed.";
            }
        },

        async rejectPending(id) {
            try {
                this.systemMessage = "Rejecting operation...";
                const res = await fetch(BACKEND_URL + "/confirm", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pending_id: id, approve: false })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Rejection failed");
                this.systemMessage = "Operation rejected.";
                this.refreshPending();
                // Update the corresponding result in results
                this.results = this.results.map(r => {
                    if (r.pending_id === id) {
                        return {
                            ...r,
                            execution_status: "rejected",
                            message: "This request has been rejected.",
                            pending_id: null // Remove pending_id so the yellow box disappears
                        };
                    }
                    return r;
                });
                if (this.pendingDetails && this.pendingDetails.id === id) {
                    this.pendingDetails = null;
                }
            } catch (e) {
                this.systemMessage = e.message || "Rejection failed.";
            }
        },

        async viewPendingDetails(id) {
            try {
                const res = await fetch(BACKEND_URL + `/pending/${id}/details`);
                const data = await res.json();
                this.pendingDetails = data.pending_operation;
            } catch (e) {
                this.systemMessage = "Failed to load details.";
            }
        },

        // --- DATABASE STATS ---
        async loadDatabaseStats() {
            try {
                const res = await fetch(BACKEND_URL + "/databases");
                const data = await res.json();
                this.dbStats = data.databases || [];
            } catch (e) {
                this.systemMessage = "Failed to load database stats.";
            }
        },

        // --- CONVERSATION HISTORY ---
        async clearConversationHistory() {
            try {
                await fetch(BACKEND_URL + "/test/clear-conversation", { method: "POST" });
                this.conversationHistory = [];
                this.systemMessage = "Conversation history cleared.";
            } catch (e) {
                this.systemMessage = "Failed to clear history.";
            }
        },

        

        async initializeDatabases() {
            this.systemMessage = "Initializing databases...";
            try {
                const res = await fetch(BACKEND_URL + "/databases/init", { method: "POST" });
                const data = await res.json();
                this.systemMessage = data.message || "Databases initialized.";
                this.loadDatabaseStats();
            } catch (e) {
                this.systemMessage = "Initialization failed.";
            }
        },

        async checkHealth() {
            this.systemMessage = "Checking system health...";
            try {
                const res = await fetch(BACKEND_URL + "/health");
                const data = await res.json();
                this.systemMessage = data.status === "ok" ? "System healthy." : "System not healthy.";
            } catch (e) {
                this.systemMessage = "Health check failed.";
            }
        },

        // --- INIT ---
        async init() {
            this.refreshPending();
            this.loadDatabaseStats();
            // Load conversation history
            try {
                const res = await fetch(BACKEND_URL + "/test/conversation-history");
                const data = await res.json();
                this.conversationHistory = (data.history || []).map(item => ({
                    query: item.query,
                    result: item.result,
                    timestamp: item.timestamp
                }));
            } catch {}
            // Load system stats
            this.systemStats.totalQueries = this.conversationHistory.length;
        }
    }
}