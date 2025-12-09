package services

import (
	"context"
	"net/http"
	"os/exec"
	"runtime"
	"strings"
	"time"
)

type Status struct {
	Name   string
	Status string
}

func Health() ([]Status, error) {
	var statuses []Status
	for _, svc := range serviceList() {
		svcStatus := probeService(svc)
		statuses = append(statuses, Status{
			Name:   svc,
			Status: svcStatus,
		})
	}

	// HTTP-level checks (best-effort)
	httpChecks := map[string]string{
		"smartcp-http":       "http://127.0.0.1:8000/healthz",
		"bifrost-api-http":   "http://127.0.0.1:8001/healthz",
		"bifrost-back-http":  "http://127.0.0.1:8080/healthz",
	}
	for name, url := range httpChecks {
		statuses = append(statuses, Status{Name: name, Status: probeHTTP(url)})
	}

	return statuses, nil
}

func StartAll() error {
	for _, svc := range serviceList() {
		if err := startService(svc); err != nil {
			return err
		}
	}
	return nil
}

func StopAll() error {
	for _, svc := range serviceList() {
		if err := stopService(svc); err != nil {
			return err
		}
	}
	return nil
}

// --- platform helpers ---

func serviceList() []string {
	return []string{"smartcp", "bifrost-backend", "bifrost-api"}
}

func probeService(name string) string {
	switch runtime.GOOS {
	case "linux":
		out, err := exec.Command("systemctl", "is-active", name).Output()
		if err != nil {
			return "unknown"
		}
		return strings.TrimSpace(string(out))
	case "darwin":
		out, err := exec.Command("launchctl", "print", "system/"+name).CombinedOutput()
		if err != nil {
			return "unknown"
		}
		if strings.Contains(string(out), "state = running") {
			return "running"
		}
		return "loaded"
	case "windows":
		out, err := exec.Command("sc", "query", name).Output()
		if err != nil {
			return "unknown"
		}
		if strings.Contains(string(out), "RUNNING") {
			return "running"
		}
		return "stopped"
	default:
		return "unknown"
	}
}

// probeHTTP checks a health endpoint with a short timeout.
func probeHTTP(url string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return "invalid"
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "unreachable"
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return "http-ok"
	}
	return resp.Status
}

func startService(name string) error {
	switch runtime.GOOS {
	case "linux":
		return exec.Command("systemctl", "start", name).Run()
	case "darwin":
		return exec.Command("launchctl", "kickstart", "-k", "system/"+name).Run()
	case "windows":
		return exec.Command("sc", "start", name).Run()
	default:
		return nil
	}
}

func stopService(name string) error {
	switch runtime.GOOS {
	case "linux":
		return exec.Command("systemctl", "stop", name).Run()
	case "darwin":
		return exec.Command("launchctl", "stop", "system/"+name).Run()
	case "windows":
		return exec.Command("sc", "stop", name).Run()
	default:
		return nil
	}
}
