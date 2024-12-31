# Changelog

## [0.3.0](https://github.com/geopython/pygeofilter/compare/v0.2.4...v0.3.0) (2024-12-30)


### Features

* add support for OpenSearch backend ([#111](https://github.com/geopython/pygeofilter/pull/111))
* Update lark ([#110](https://github.com/geopython/pygeofilter/pull/110))


### Bug Fixes

* Handle boolean in ecql like cql_text ([#108](https://github.com/geopython/pygeofilter/pull/108))
* Fix compatibility with i386 ([#107](https://github.com/geopython/pygeofilter/pull/107))
* add FES parser import shortcut as other filter languages  ([#102](https://github.com/geopython/pygeofilter/pull/102))


### Miscellaneous Chores

* release 0.3.0 ([48de1f1](https://github.com/geopython/pygeofilter/commit/48de1f128c4956a99d6760487146636122e119a3))

## [0.2.4](https://github.com/geopython/pygeofilter/compare/v0.2.3...v0.2.4) (2024-07-10)


### Bug Fixes

* bumping version to 0.2.4 ([21bc095](https://github.com/geopython/pygeofilter/commit/21bc0957c84244b7d39dbe164f00d143d952c684))

## [0.2.3](https://github.com/geopython/pygeofilter/compare/v0.2.2...v0.2.3) (2024-07-10)


### Bug Fixes

* adding dependency for publishing packages ([249926e](https://github.com/geopython/pygeofilter/commit/249926ef2ebe264b616ce0f039a8b0e1b8626dda))

## [0.2.2](https://github.com/geopython/pygeofilter/compare/v0.2.1...v0.2.2) (2024-07-10)


### Bug Fixes

* [#85](https://github.com/geopython/pygeofilter/issues/85) ([2f1a38f](https://github.com/geopython/pygeofilter/commit/2f1a38f8bc9dfe2ebf5c318c6121d7f51029a9cf))
* Addresses [#95](https://github.com/geopython/pygeofilter/issues/95). ([d51dbb0](https://github.com/geopython/pygeofilter/commit/d51dbb0eb7a1066bd97b81cffe99da11ebf3cba4))
* Addresses [#95](https://github.com/geopython/pygeofilter/issues/95). ([2a51990](https://github.com/geopython/pygeofilter/commit/2a519904c4ac408fabb39459104efcc3e09f3a40))
* Bump pre-commit dependencies ([90f4aaa](https://github.com/geopython/pygeofilter/commit/90f4aaaafe873c69b0ccd91e897a9ff218ef5110))
* Bump pre-commit dependencies ([64f7f96](https://github.com/geopython/pygeofilter/commit/64f7f962476665d4ae4eed750099a6c887ad21ca))
* Bump pre-commit dependencies ([11f1f9a](https://github.com/geopython/pygeofilter/commit/11f1f9ab71811da758aa67b13aeb2f0cce7aaa10))
* Enable custom handling of undefined field attr in to_filter ([23f172c](https://github.com/geopython/pygeofilter/commit/23f172cf1dd1ddb19791a761f128b001e887b361))
* Enable custom handling of undefined field attr in to_filter ([f0c7e9f](https://github.com/geopython/pygeofilter/commit/f0c7e9f36d55d80e1d17917a627ae5547c80363c))
* Enable custom handling of undefined field attr in to_filter ([d829c6b](https://github.com/geopython/pygeofilter/commit/d829c6be5254a45689d8bcdb52b28b8a5ed3b5b2))
* Support prefixed attribute names in cql2-text and ecql parsing ([dbe4e9e](https://github.com/geopython/pygeofilter/commit/dbe4e9e5c0c48698f312e1cc023a43ea78391f60))
* Support prefixed attribute names in cql2-text and ecql parsing ([5318c6b](https://github.com/geopython/pygeofilter/commit/5318c6bcf6e2620d39c8bc52fa13cc40e02274ac))
* Support prefixed attribute names in cql2-text and ecql parsing ([122a5a6](https://github.com/geopython/pygeofilter/commit/122a5a6c5ba746a51bf9eb36a5d9617201d19123))
* Updating release-please to v4 ([11757ec](https://github.com/geopython/pygeofilter/commit/11757eca4a7ba71fbca575636117b6eb8b3c9e53))

### [0.2.1](https://www.github.com/geopython/pygeofilter/compare/v0.2.0...v0.2.1) (2023-02-16)


### Bug Fixes

* dt naivety ([08fb5f5](https://www.github.com/geopython/pygeofilter/commit/08fb5f5f8b0a5ee39443a6233d558bbacadb5acb))
* order of date/datetime checking in native evaluator ([d37d7c8](https://www.github.com/geopython/pygeofilter/commit/d37d7c8cb483fdb9ff53ff9f871d5a8f85a227e1))
* pinning sqlalchemy to version < 2.0.0 ([6e67239](https://www.github.com/geopython/pygeofilter/commit/6e67239eb1af9a77599bbbc8cee211c9f906d95e))
* timezone handling for dates ([6c0e5c1](https://www.github.com/geopython/pygeofilter/commit/6c0e5c17ce5dde2dc541ccd6411c55d2a86e52ec))

## [0.2.0](https://www.github.com/geopython/pygeofilter/compare/v0.1.2...v0.2.0) (2022-10-17)


### Features

* adding initial elasticsearch implmentation ([2ccfa02](https://www.github.com/geopython/pygeofilter/commit/2ccfa02d5fcf1ee1f3be76f5cf375ace2556fa6c))

### [0.1.2](https://www.github.com/geopython/pygeofilter/compare/v0.1.1...v0.1.2) (2022-04-21)


### Bug Fixes

* Allowing intervals to actually contain subnodes ([83b7c63](https://www.github.com/geopython/pygeofilter/commit/83b7c63ad9233a9ed600f061d3b8e074291dcb8c))

### [0.1.1](https://www.github.com/geopython/pygeofilter/compare/v0.1.0...v0.1.1) (2022-02-08)


### Bug Fixes

* Fixing compatibility issues with Python 3.6 type checking ([ad7ddd7](https://www.github.com/geopython/pygeofilter/commit/ad7ddd7a332f838fa284e1493f0d3cc15036ad95))
* Improved typing ([2272b3b](https://www.github.com/geopython/pygeofilter/commit/2272b3b9371ff90fe5cbc9b8f84cbf6bb5cca76a))
* Improving structure of CI for type checking ([fb755a3](https://www.github.com/geopython/pygeofilter/commit/fb755a3859baf3a07f57938da2259b5c3fb74575))
* Improving typing ([6c3584b](https://www.github.com/geopython/pygeofilter/commit/6c3584b3961fe90cc07f08f6cc8f2256112850f3))
* Improving typing on CQL2 JSON ([e0747aa](https://www.github.com/geopython/pygeofilter/commit/e0747aa2d0dbcaedd49bd9bcf30e702da68aaa37))
* more concise type checking ([87e46a2](https://www.github.com/geopython/pygeofilter/commit/87e46a2c325fb5f1c1c92408369efdf263f387db))
* mypy dependency installation (using --non-interactive) ([84a1175](https://www.github.com/geopython/pygeofilter/commit/84a11752c48773650a063a767eb97a1fa149b0ac))
* Split up Django spatial filters ([484e0b3](https://www.github.com/geopython/pygeofilter/commit/484e0b3db483db76b6456593a33ee8598f72813d))

## [0.1.0](https://www.github.com/geopython/pygeofilter/compare/v0.1.0...v0.1.0) (2021-11-18)


### Features

* Fixing release-please package name ([2b666fc](https://www.github.com/geopython/pygeofilter/commit/2b666fc5b09c2ff15fa954f035a342542aa3577f))


### Miscellaneous Chores

* release 0.1.0 ([d5e4971](https://www.github.com/geopython/pygeofilter/commit/d5e49718f7f2c7936649217b286ebad42b168a23))

## 0.1.0 (2021-11-18)


### Features

* Merge pull request [#34](https://www.github.com/geopython/pygeofilter/issues/34) from geopython/cql2_json ([5d439b2](https://www.github.com/geopython/pygeofilter/commit/5d439b277e12b883f3132d4972d2979a8aefd92e))
