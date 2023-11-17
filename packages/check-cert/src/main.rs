// Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
// conditions defined in the file COPYING, which is part of this source code package.

use anyhow::Result;
use check_cert::{checker, fetcher, output};
use clap::Parser;
use std::time::Duration as StdDuration;
use time::Duration;
use x509_parser::certificate::X509Certificate;
use x509_parser::prelude::FromDer;

#[derive(Parser, Debug)]
#[command(about = "check_cert")]
struct Args {
    /// URL to check
    #[arg(short, long)]
    url: String,

    /// Port
    #[arg(short, long, default_value_t = 443)]
    port: u16,

    /// Set timeout in seconds
    #[arg(long, default_value_t = 10)]
    timeout: u64,

    /// Warn if certificate expires in n days
    #[arg(long, default_value_t = 30)]
    warn: u32,

    /// Crit if certificate expires in n days
    #[arg(long, default_value_t = 0)]
    crit: u32,

    /// Disable SNI extension
    #[arg(long, action = clap::ArgAction::SetTrue)]
    disable_sni: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    if args.warn < args.crit {
        eprintln!("crit limit larger than warn limit");
        std::process::exit(1);
    }

    let der = fetcher::fetch_server_cert(
        &args.url,
        &args.port,
        if args.timeout == 0 {
            None
        } else {
            Some(StdDuration::new(args.timeout, 0))
        },
        !args.disable_sni,
    )?;

    let (_rem, cert) = X509Certificate::from_der(&der)?;
    let out = output::Output::from(vec![checker::check_validity_not_after(
        cert.tbs_certificate.validity().time_to_expiration(),
        checker::LowerLevels::warn_crit(args.warn * Duration::DAY, args.crit * Duration::DAY),
        cert.tbs_certificate.validity().not_after,
    )]);
    println!("HTTP {}", out);
    std::process::exit(match out.state {
        checker::State::Ok => 0,
        checker::State::Warn => 1,
        checker::State::Crit => 2,
        checker::State::Unknown => 3,
    })
}
