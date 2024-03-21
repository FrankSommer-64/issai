[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/FrankSommer-64/issai">
    <img src="images/issai.png" alt="Logo" width="128" height="128">
  </a>

<h3 align="center">Issai</h3>
  <p align="center">
    Run, export and import tests managed by Kiwi TCMS
    <br />
    <a href="https://github.com/FrankSommer-64/issai"><strong>Documentation</strong></a>
    <br />
    <br />
    <a href="https://github.com/FrankSommer-64/issai/issues">Report Bug</a>
    ·
    <a href="https://github.com/FrankSommer-64/issai/issues">Request Feature</a>
  </p>
</div>


## About The Project

Issai is a customizable framework to run test plans specified in Kiwi test case management system (TCMS).<br/>
The name issai was chosen, because it denotes a small sort of kiwi fruit.<br/>
Kiwi TCMS offers attributes to specify automated test plans and test cases,
however, it does not provide the functionality to do so.<br/>
The framework also implements export and import functionality, which is not contained in Kiwi TCMS either.<br/>
Exports are useful for backing up test specifications and running tests offline without connection to Kiwi TCMS.<br/>
Imports can be used to restore test specifications and allows to create test specifications
in another tool or a document.<br/>


## Getting Started

### Prerequisites

Since Issai doesn't offer test management functionality, you need access to a Kiwi TCMS instance.
Issai needs Python 3.


### Installation

1. pip install issai
2. Enter URL and credentials in file .tcms.conf in your home directory to access Kiwi TCMS using XML-RPC
3. Configure issai according to your needs in directory .config/issai under your home directory.



## Usage

Issai offers a GUI for local configuration and development on test automation. Start the GUI with <pre>issai_gui</pre>.

For automated tasks, Issai's command line interface can be used:
<ul>
  <li>Run a test plan: <pre>issai_run --plan mytestplan --product-version "v0.8" --product-build "240120"</pre></li>
  <li>Export a product: <pre> issai_export --product myproduct /tmp/issai-export</pre></li>
  <li>Import a test result: <pre> issai_import /tmp/myproduct/plan_24_result.toml</pre></li>
</ul>



## Roadmap

- [ ] v0.7 full functionality to run tests
- [ ] v0.8 full functionality for import and export, CI integration
- [ ] v0.9 Windows support, localization, complete system test

See the [open issues](https://github.com/FrankSommer-64/issai/issues) for a full list of proposed features (and known issues).


## Contributing

Any contributions you make are **greatly appreciated**.



## License

Distributed under the MIT License. See [LICENSE][license-url] for more information.



## Contact

Frank Sommer - Frank.Sommer@sherpa-software.de

Project Link: [https://github.com/FrankSommer-64/issai](https://github.com/FrankSommer-64/issai)

[contributors-shield]: https://img.shields.io/github/contributors/FrankSommer-64/coaly.svg?style=for-the-badge
[contributors-url]: https://github.com/FrankSommer-64/coaly/graphs/contributors
[issues-shield]: https://img.shields.io/github/issues/FrankSommer-64/coaly.svg?style=for-the-badge
[issues-url]: https://github.com/FrankSommer-64/coaly/issues
[license-shield]: https://img.shields.io/github/license/FrankSommer-64/coaly.svg?style=for-the-badge
[license-url]: https://github.com/FrankSommer-64/coaly/blob/master/LICENSE
