// Aodı-AgentX — netmgr: high-performance network & execution manager (stdlib only).
// Endpoints:
//
//	GET /health                     → status + uptime
//	GET /sysinfo                    → cpu/mem/os (cross-platform best effort)
//	GET /ports?host=&from=&to=      → concurrent port scan (goroutines)
//	GET /probe?url=                 → HTTP reachability probe (Ollama-friendly)
package main

import (
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

var startedAt = time.Now()

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func health(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{
		"status":         "ok",
		"service":        "agentx.netmgr",
		"version":        "1.0.0",
		"uptime_seconds": int(time.Since(startedAt).Seconds()),
	})
}

func sysinfo(w http.ResponseWriter, r *http.Request) {
	info := map[string]any{
		"os":         runtime.GOOS + "/" + runtime.GOARCH,
		"num_cpu":    runtime.NumCPU(),
		"goroutines": runtime.NumGoroutine(),
		"memory":     memInfo(),
	}
	writeJSON(w, 200, info)
}

func memInfo() map[string]any {
	out := map[string]any{}
	switch runtime.GOOS {
	case "linux":
		if b, err := os.ReadFile("/proc/meminfo"); err == nil {
			var total, avail uint64
			s := string(b)
			fmt.Sscanf(s, "MemTotal: %d", &total)
			_ = avail
			for i := 0; i < len(s); i++ {
				if len(s[i:]) > 12 && s[i:i+12] == "MemAvailable" {
					fmt.Sscanf(s[i:], "MemAvailable: %d", &avail)
					break
				}
			}
			out["total_kb"] = total
			out["available_kb"] = avail
		}
	default:
		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		out["go_heap_alloc_mb"] = m.HeapAlloc / 1024 / 1024
	}
	return out
}

func ports(w http.ResponseWriter, r *http.Request) {
	host := r.URL.Query().Get("host")
	from, _ := strconv.Atoi(r.URL.Query().Get("from"))
	to, _ := strconv.Atoi(r.URL.Query().Get("to"))
	if host == "" || to == 0 {
		writeJSON(w, 400, map[string]string{"error": "host و from/to مطلوبة"})
		return
	}
	if host == "localhost" {
		host = "127.0.0.1"
	}
	if from < 1 {
		from = 1
	}
	if to > 65535 {
		to = 65535
	}
	if to-from > 3000 {
		writeJSON(w, 400, map[string]string{"error": "نطاق واسع جداً (الحد 3000)"})
		return
	}
	type res struct {
		Port int    `json:"port"`
		Open bool   `json:"open"`
		Note string `json:"note,omitempty"`
	}
	opened := make([]res, 0)
	var mu sync.Mutex
	var scanned int32
	start := time.Now()
	sem := make(chan struct{}, 200)
	var wg sync.WaitGroup
	for p := from; p <= to; p++ {
		wg.Add(1)
		sem <- struct{}{}
		go func(port int) {
			defer wg.Done()
			defer func() { <-sem }()
			conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), time.Second)
			atomic.AddInt32(&scanned, 1)
			if err == nil {
				note := ""
				if port == 11434 {
					note = "ollama"
				}
				if port == 22 {
					note = "ssh"
				}
				if port == 80 || port == 443 {
					note = "web"
				}
				mu.Lock()
				opened = append(opened, res{Port: port, Open: true, Note: note})
				mu.Unlock()
				_ = conn.Close()
			}
		}(p)
	}
	wg.Wait()
	writeJSON(w, 200, map[string]any{
		"host": host, "scanned": scanned,
		"open_count": len(opened), "open": opened,
		"elapsed_ms": time.Since(start).Milliseconds(),
	})
}

func probe(w http.ResponseWriter, r *http.Request) {
	url := r.URL.Query().Get("url")
	if url == "" {
		writeJSON(w, 400, map[string]string{"error": "url مطلوبة"})
		return
	}
	client := &http.Client{Timeout: 6 * time.Second}
	t0 := time.Now()
	resp, err := client.Get(url)
	if err != nil {
		writeJSON(w, 200, map[string]any{"url": url, "ok": false, "error": err.Error()})
		return
	}
	defer resp.Body.Close()
	writeJSON(w, 200, map[string]any{
		"url": url, "ok": true, "status_code": resp.StatusCode,
		"latency_ms": time.Since(t0).Milliseconds(),
	})
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", health)
	mux.HandleFunc("/sysinfo", sysinfo)
	mux.HandleFunc("/ports", ports)
	mux.HandleFunc("/probe", probe)
	addr := ":7231"
	if v := os.Getenv("NETMGR_ADDR"); v != "" {
		addr = v
	}
	server := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	fmt.Println("agentx.netmgr v1.0.0 listening on", addr)
	_ = server.ListenAndServe()
}
