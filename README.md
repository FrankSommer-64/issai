# Ariadne

[![Test Status](https://github.com/rust-random/rand/workflows/Tests/badge.svg?event=push)](https://github.com/rust-random/rand/actions)
[![Crate](https://img.shields.io/crates/v/rand.svg)](https://crates.io/crates/rand)
[![Book](https://img.shields.io/badge/book-master-yellow.svg)](https://rust-random.github.io/book/)
[![API](https://img.shields.io/badge/api-master-yellow.svg)](https://rust-random.github.io/rand/rand)
[![API](https://docs.rs/rand/badge.svg)](https://docs.rs/rand)
[![Minimum rustc version](https://img.shields.io/badge/rustc-1.36+-lightgray.svg)](https://github.com/rust-random/rand#rust-version-requirements)

A Rust library for logging and tracing.
There are various libraries for that purpose around, but especially in situations where direct debugging
isn't possible or spurious errors must be tracked down, Ariadne can be worth a try
due to some unique features:

- Event based output mode for log and trace messages. Output mode means filtering of messages according to their
  associated level (e.g. error or warning). Usually, the output mode is defined once upon application start and on a
  per-module basis. In Ariadne, the default output mode is set upon application start and may change whenever
  configurable events like a certain function call or structure instantiation occur.
- Configurable formatting of log and trace messages
- Support for output resource types file, memory mapped file, console and network
- File based resources may be level-, thread-, process- or application speficic
- Built-in rollover of file resources based either on file size or time

Documentation:

-   [The Rust Rand Book](https://rust-random.github.io/book)
-   [API reference (master branch)](https://rust-ariadne.github.io/ariadne)
-   [API reference (docs.rs)](https://docs.rs/ariadne)


## Usage

Add this to your `Cargo.toml`:

```toml
[dependencies]
ariadne = "0.9.0"
```

To get started using Ariadne, view the sample configuration file in the doc folder.


## Versions

Ariadne is still under construction.

Current Ariadne versions are:

-   Version 0.9 is feature complete, but still widely untested.

A detailed [changelog](CHANGELOG.md) is available for releases.


### Rust version requirements

Ariadne complies to the 2021 Rust standard and requires **Rustc version 1.36 or greater**.

## Crate Features

Ariadne is built with this features enabled by default:

-   `core` enables functionality without network support

Optional, the following feature can be added:

-   `net` enables network functionality including a dedicated log and trace server, implied by `all`

# License

Ariadne is distributed under the terms of both the MIT license and the
Apache License (Version 2.0).

See [LICENSE-APACHE](LICENSE-APACHE) and [LICENSE-MIT](LICENSE-MIT), and
[COPYRIGHT](COPYRIGHT) for details.
