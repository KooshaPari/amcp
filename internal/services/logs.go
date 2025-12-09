package services

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
)

func TailLogs() error {
	switch runtime.GOOS {
	case "linux":
		// Tail journald for all managed services
		return exec.Command("journalctl", "-fu", "smartcp", "-fu", "bifrost-backend", "-fu", "bifrost-api").Run()
	case "darwin":
		return exec.Command("log", "stream", "--predicate", "subsystem == \"com.smartcp\"").Run()
	case "windows":
		return exec.Command("powershell", "-Command", "Get-EventLog -LogName Application -Source smartcp -Newest 50 -Wait").Run()
	default:
		fmt.Println("log tailing not supported on this platform")
		return nil
	}
}

// helper
func logWriter(_ string) *os.File {
	return os.Stdout
}
