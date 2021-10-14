// Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
// or more contributor license agreements. Licensed under the Elastic License;
// you may not use this file except in compliance with the Elastic License.

// Code generated by beats/dev-tools/cmd/asset/asset.go - DO NOT EDIT.

package gcp

import (
	"github.com/elastic/beats/v7/libbeat/asset"
)

func init() {
	if err := asset.SetFields("metricbeat", "gcp", asset.ModuleFieldsPri, AssetGcp); err != nil {
		panic(err)
	}
}

// AssetGcp returns asset data.
// This is the base64 encoded zlib format compressed contents of module/gcp.
func AssetGcp() string {
	return "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"
}
