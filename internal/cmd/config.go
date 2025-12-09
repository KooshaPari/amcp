package cmd

import (
    "fmt"

    "github.com/spf13/cobra"
    "smartcp/internal/config"
)

var configCmd = &cobra.Command{
    Use:   "config",
    Short: "Get or set config values (writes shared user config)",
}

var configGetCmd = &cobra.Command{
    Use:   "get [key]",
    Short: "Get a config value",
    Args:  cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        cfg, err := config.Load()
        if err != nil {
            return err
        }
        val := cfg.Get(args[0])
        fmt.Println(val)
        return nil
    },
}

var configSetCmd = &cobra.Command{
    Use:   "set [key] [value]",
    Short: "Set a config value (and persist)",
    Args:  cobra.ExactArgs(2),
    RunE: func(cmd *cobra.Command, args []string) error {
        cfg, err := config.Load()
        if err != nil {
            return err
        }
        if err := cfg.Set(args[0], args[1]); err != nil {
            return err
        }
        return config.Save(cfg)
    },
}

func init() {
    configCmd.AddCommand(configGetCmd)
    configCmd.AddCommand(configSetCmd)
}
