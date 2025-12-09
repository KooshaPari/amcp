package cmd

import (
    "github.com/spf13/cobra"
    "smartcp/internal/services"
)

var servicesCmd = &cobra.Command{
    Use:   "services",
    Short: "Control native services (systemd/launchd/WinSvc)",
}

var servicesStartCmd = &cobra.Command{
    Use:   "start",
    Short: "Start SmartCP and Bifrost services",
    RunE: func(cmd *cobra.Command, args []string) error {
        return services.StartAll()
    },
}

var servicesStopCmd = &cobra.Command{
    Use:   "stop",
    Short: "Stop SmartCP and Bifrost services",
    RunE: func(cmd *cobra.Command, args []string) error {
        return services.StopAll()
    },
}

func init() {
    servicesCmd.AddCommand(servicesStartCmd)
    servicesCmd.AddCommand(servicesStopCmd)
}
