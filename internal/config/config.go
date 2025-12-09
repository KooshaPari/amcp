package config

import (
    "gopkg.in/yaml.v3"
    "io/ioutil"
    "os"
    "path/filepath"
)

const DefaultPath = ".config/smartcp/config.yml"

// Config is a thin wrapper; you can expand with typed fields as needed.
type Config struct {
    raw map[string]interface{}
}

func Load() (*Config, error) {
    path := resolvePath()
    data, err := ioutil.ReadFile(path)
    if err != nil {
        return &Config{raw: map[string]interface{}{}}, nil
    }
    m := map[string]interface{}{}
    if err := yaml.Unmarshal(data, &m); err != nil {
        return nil, err
    }
    return &Config{raw: m}, nil
}

func Save(c *Config) error {
    path := resolvePath()
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    out, err := yaml.Marshal(c.raw)
    if err != nil {
        return err
    }
    return ioutil.WriteFile(path, out, 0o644)
}

func (c *Config) Get(key string) interface{} {
    return c.raw[key]
}

func (c *Config) Set(key string, val interface{}) error {
    c.raw[key] = val
    return nil
}

func InitInteractive() error {
    // Stub: in a real implementation, load TUI/interactive prompts and then Save.
    c := &Config{raw: map[string]interface{}{
        "api": map[string]interface{}{
            "bifrost_url": "http://localhost:8080/graphql",
        },
    }}
    return Save(c)
}

func resolvePath() string {
	if p := os.Getenv("SMARTCP_CONFIG"); p != "" {
		return p
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return DefaultPath
	}
	return filepath.Join(home, DefaultPath)
}
