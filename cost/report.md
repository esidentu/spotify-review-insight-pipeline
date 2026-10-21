# Pilot cost and runtime report

This report is calculated offline from saved call usage, run measurements, and editable rates.

## Saved call usage

| Run | Phase | Role | Provider | Model | Effort | Prompt version | Schema version | Batch sizes | Workers | Attempts | Outcomes | Input tokens | Cached input tokens | Output tokens | Billed requests | Known cost | Status |
|---|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|---:|---:|---|---|
| adversarial-checks-2026-10-20 | finalization | enrich (primary) | typesafe | jev-1.13.0 | none | adversarial-check-v1 | typed-response-v1 | 1 | 1 | 1 | succeeded: 1 | 1025 | 0 | 162 | 1 | USD 0.000043 | priced usage |
| adversarial-checks-2026-10-20 | finalization | verify | typesafe | jev-1.13.0 | none | adversarial-check-v1 | typed-response-v1 | 1 | 1 | 1 | succeeded: 1 | 449 | 0 | 20 | 1 | USD 0.000019 | priced usage |
| adversarial-checks-2026-10-21 | finalization | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v2 | typed-response-v1 | 1 | 1 | 1 | succeeded: 1 | 1257 | 0 | 160 | 1 | USD 0.000053 | priced usage |
| adversarial-checks-2026-10-21 | finalization | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | typed-response-v1 | 1 | 1 | 1 | succeeded: 1 | 449 | 0 | 20 | 1 | USD 0.000019 | priced usage |
| batch-benchmark-golden50 | cold | enrich (primary) | typesafe | jev-latest | none | spotify-enrich-batch5-benchmark-v1 | record-v1 | 5 | 1 | 1 | failed: 1 | 0 | 0 | 0 | 1 | unavailable | partial or unresolved |
| batch-benchmark-golden50-w1 | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-batch5-benchmark-v1 | record-v1 | 5 | 1 | 10 | succeeded: 10 | 53079 | 0 | 8662 | 10 | USD 0.002229 | priced usage |
| batch-benchmark-golden50-w2 | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-batch5-benchmark-v1 | record-v1 | 5 | 2 | 10 | succeeded: 10 | 53079 | 0 | 8663 | 10 | USD 0.002229 | priced usage |
| cold-100-20261020T183808Z | cold | enrich (primary) | typesafe | jev-latest | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 1 | failed: 1 | 0 | 0 | 0 | 1 | unavailable | partial or unresolved |
| cold-100-20261020T184149Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 100 | succeeded: 100 | 101887 | 0 | 16059 | 100 | USD 0.004279 | priced usage |
| cold-100-20261020T184149Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 1 | 10 | succeeded: 10 | 4503 | 0 | 200 | 10 | USD 0.000189 | priced usage |
| cold-10000-20261020T191621Z | cold | enrich (primary) | typesafe | jev-latest | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 1 | failed: 1 | 0 | 0 | 0 | 1 | unavailable | partial or unresolved |
| cold-10000-20261020T191948Z | cold | enrich (primary) | typesafe | jev-latest | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 1 | failed: 1 | 0 | 0 | 0 | 1 | unavailable | partial or unresolved |
| cold-10000-20261020T192125Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 987 | succeeded: 987 | 1004903 | 0 | 158431 | 987 | USD 0.042206 | priced usage |
| cold-10000-20261020T192530Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 6982 | succeeded: 6982 | 7116843 | 0 | 1120975 | 6982 | USD 0.298907 | priced usage |
| cold-10000-20261020T192530Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 1 | 797 | succeeded: 797 | 364069 | 0 | 15940 | 797 | USD 0.015291 | priced usage |
| cold-100000-20261020T213754Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 2 | 69651 | succeeded: 69651 | 71081049 | 0 | 11184829 | 69651 | USD 2.985404 | priced usage |
| cold-100000-20261020T213754Z | cold | enrich (primary) | typesafe | jev-latest | none | spotify-enrich-v1 | record-v1 | 1 | 2 | 9 | failed: 9 | 0 | 0 | 0 | 9 | unavailable | partial or unresolved |
| cold-100000-20261020T213754Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 2 | 6965 | succeeded: 6965 | 3190014 | 0 | 139300 | 6965 | USD 0.133981 | priced usage |
| cold-500-20261020T185608Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 379 | succeeded: 379 | 385992 | 0 | 60846 | 379 | USD 0.016212 | priced usage |
| cold-500-20261020T185608Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 1 | 38 | succeeded: 38 | 17154 | 0 | 760 | 38 | USD 0.000720 | priced usage |
| cold-custom-0736cdcd005a-20261021T015103Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v2 | record-v1 | 1 | 2 | 30 | succeeded: 30 | 37169 | 0 | 4818 | 30 | USD 0.001561 | priced usage |
| cold-custom-0736cdcd005a-20261021T015103Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 2 | 3 | succeeded: 3 | 1338 | 0 | 60 | 3 | USD 0.000056 | priced usage |
| cold-custom-2e1f03ced275-20261021T020307Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v2 | record-v1 | 1 | 2 | 30 | succeeded: 30 | 37169 | 0 | 4818 | 30 | USD 0.001561 | priced usage |
| cold-custom-2e1f03ced275-20261021T020307Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 2 | 3 | succeeded: 3 | 1334 | 0 | 60 | 3 | USD 0.000056 | priced usage |
| cold-custom-c884ac3b9be5-20261021T022408Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v2 | record-v1 | 1 | 1 | 100 | succeeded: 100 | 125087 | 0 | 16054 | 100 | USD 0.005254 | priced usage |
| cold-custom-c884ac3b9be5-20261021T022408Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 1 | 10 | succeeded: 10 | 4502 | 0 | 200 | 10 | USD 0.000189 | priced usage |
| cold-custom-f5a801c0b3b7-20261021T014956Z | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v2 | record-v1 | 1 | 2 | 30 | succeeded: 30 | 37169 | 0 | 4818 | 30 | USD 0.001561 | priced usage |
| cold-custom-f5a801c0b3b7-20261021T014956Z | cold | verify | typesafe | jev-1.13.0 | none | spotify-verify-v1 | record-v1 | 1 | 2 | 3 | succeeded: 3 | 1339 | 0 | 60 | 3 | USD 0.000056 | priced usage |
| dashboard-finalization-100000 | finalization | group | typesafe | jev-1.13.0 | none | spotify-group-and-recommendation-v1 | choice-v1 | 1 | 1 | 1 | succeeded: 1 | 3180 | 0 | 101 | 1 | USD 0.000134 | priced usage |
| dashboard-finalization-100000 | finalization | group | typesafe | jev-latest | none | spotify-group-and-recommendation-v1 | choice-v1 | 1 | 1 | 1 | failed: 1 | 0 | 0 | 0 | 0 | unavailable | priced usage |
| dashboard-finalization-100000 | finalization | memo | typesafe | jev-1.13.0 | none | spotify-group-and-recommendation-v1 | choice-v1 | 1 | 1 | 1 | succeeded: 1 | 3196 | 0 | 95 | 1 | USD 0.000134 | priced usage |
| worker-comparison-golden50-w1 | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 1 | 50 | succeeded: 50 | 50825 | 0 | 8027 | 50 | USD 0.002135 | priced usage |
| worker-comparison-golden50-w2 | cold | enrich (primary) | typesafe | jev-1.13.0 | none | spotify-enrich-v1 | record-v1 | 1 | 2 | 50 | succeeded: 50 | 50825 | 0 | 8027 | 50 | USD 0.002135 | priced usage |

**Known API subtotal:** USD 3.516613.
**Calls with incomplete or missing usage:** 13.

## Usage dashboard reconciliation

These notes record dashboard readings and checks of failed calls. TypeSafe warns that usage may be delayed. Failed requests keep their estimated reserve against the local cap until token usage appears; a dashboard total that trails the call ledger is not treated as a final reconciliation.

- Call `a18612f3-974b-4ce2-ba98-2d6a199e1833`: User reported no usage on TypeSafe dashboard after the earlier connection failure. Reserved against the local cap: USD 0.000089712.
- Call `034d6cdd-7dbc-464c-b6ee-007cc9f88ac3`: The Jev request returned TypeSafeAPIConnectionError. A no-cost TypeSafe model-list diagnostic then failed with ConnectError: getaddrinfo failed, confirming the execution environment could not resolve the API host. The later model-list diagnostic succeeded after network access was enabled. Estimated request reserve remains held against the cap. Reserved against the local cap: USD 0.000091350.
- Call `ea6de1cb-b8ce-4c04-917c-2da104dd2407`: The resumed Jev request returned TypeSafeAPIConnectionError. A no-cost TypeSafe model-list diagnostic then failed with ConnectError: getaddrinfo failed, confirming the execution environment could not resolve the API host. The later model-list diagnostic succeeded after network access was enabled. Estimated request reserve remains held against the cap. Reserved against the local cap: USD 0.000091350.
- Dashboard snapshot: After the 10,000-row cold and warm runs, the TypeSafe Usage page (All traffic, Last 24 hours) showed estimated spend USD 0.2166, 5,967,246 tokens, and 5,088 requests. The page warns that usage stats may be delayed. The local pilot ledger calculates USD 0.377804742 in known Jev token charges across successful responses, so the dashboard is not yet fully reconciled to the run ledger.
- Call `e3605eb7-e632-435c-934c-7f364e890a80`: The five-review TypeSafe benchmark call returned TypeSafeAPIConnectionError. A local DNS lookup for api.typesafe.ai then failed with getaddrinfo failed, confirming no API host resolution and no request dispatch. The conservative reservation remains held against the USD 8 local cap. Reserved against the local cap: USD 0.000702744.
- Dashboard snapshot: After the user flushed the Windows DNS cache, standard project-runner lookups still failed. With network access granted to the specific diagnostic/benchmark commands, api.typesafe.ai resolved, an authenticated no-cost model-list request succeeded, and the paired 50-review one-worker/two-worker benchmark completed with usage for all 20 calls. No OS DNS server settings were changed; the earlier failed call remains separately reserved.
- Call `2e937abb-ec15-4e1f-85ea-19444aba98be`: The paid call returned TypeSafeAPIConnectionError in 0.013/0.018 seconds with no provider request ID. A no-cost TypeSafe model-list call in the same standard runner environment failed with getaddrinfo failed; the same diagnostic succeeded when network access was enabled. Classify as not dispatched due to DNS/network restriction; retain full estimated reserve against the USD 8 cap. Reserved against the local cap: USD 0.000090300.
- Call `5f5aab9e-89c0-4bb2-a38a-01837dce6842`: The paid call returned TypeSafeAPIConnectionError in 0.013/0.018 seconds with no provider request ID. A no-cost TypeSafe model-list call in the same standard runner environment failed with getaddrinfo failed; the same diagnostic succeeded when network access was enabled. Classify as not dispatched due to DNS/network restriction; retain full estimated reserve against the USD 8 cap. Reserved against the local cap: USD 0.000096264.
- Call `fc39c6fc-7b6d-48d1-ae53-68c0c9860f82`: Two-worker call returned TypeSafeAPIConnectionError after about 76.9 seconds, with no provider request ID or usage tokens. A no-cost TypeSafe model-list call succeeded afterward. Provider dashboard still displayed an older total and warns that usage may be delayed, so usage is unknown; preserve the full estimated reserve and separately reserve the next attempt. Reserved against the local cap: USD 0.000089838.
- Call `a3bbfe77-be3e-44c6-83c9-0e42d0e9393a`: Two-worker call returned TypeSafeAPIConnectionError after about 76.9 seconds, with no provider request ID or usage tokens. A no-cost TypeSafe model-list call succeeded afterward. Provider dashboard still displayed an older total and warns that usage may be delayed, so usage is unknown; preserve the full estimated reserve and separately reserve the next attempt. Reserved against the local cap: USD 0.000092064.
- Call `b31b0473-49c5-4e5d-89f6-4d8d6c258c1a`: Two-worker calls returned TypeSafeAPIConnectionError after about 219 seconds, with no provider request ID or usage tokens. A no-cost TypeSafe model-list call succeeded afterward; the usage page still shows an older delayed total. Usage is unknown; preserve each full estimated reserve and reserve any resumed attempt separately. Reserved against the local cap: USD 0.000093576.
- Call `518ac7e4-6f59-4ab7-81fd-40f700fd0c8b`: Two-worker calls returned TypeSafeAPIConnectionError after about 219 seconds, with no provider request ID or usage tokens. A no-cost TypeSafe model-list call succeeded afterward; the usage page still shows an older delayed total. Usage is unknown; preserve each full estimated reserve and reserve any resumed attempt separately. Reserved against the local cap: USD 0.000090132.
- Call `c6b32aaa-81b7-4a7f-bfbc-9b29a24cc466`: Two-worker request returned TypeSafeAPITimeoutError with no provider request ID or usage tokens. TypeSafe usage dashboard still shows an older delayed total. Usage is unknown; retain the full estimated reserve and reserve a resumed request separately. Reserved against the local cap: USD 0.000091980.
- Call `faf90852-b5a7-428f-8009-ed1b7e23beec`: Two-worker request returned TypeSafeAPITimeoutError without provider request ID or usage tokens; the TypeSafe dashboard warns that usage may be delayed. Usage is unknown, so retain the full estimated reserve and separately reserve a resumed request. Reserved against the local cap: USD 0.000095046.
- Call `e8dc567e-1207-49d7-aa4a-026af2ef131a`: Request returned TypeSafeAPITimeoutError without provider request ID or usage tokens. The SDK default timeout was 10 seconds; usage remains uncertain and the dashboard is delayed. Retain the full reserve. The runner timeout is now raised to 60 seconds for future attempts. Reserved against the local cap: USD 0.000103824.
- Dashboard snapshot: After the 100,000-review run, refreshed TypeSafe Usage page (All traffic, Last 24 hours) showed estimated spend USD 3.228, 88,910,604 tokens, and 75,711 requests. The page warns usage statistics may be delayed. Local call ledger known subtotal is USD 3.505917324; dashboard and ledger are not reconciled.
- Call `89c8a8ac-72bc-4212-9e54-5110b38200bb`: SDK raised TypeSafeAPIConnectionError with getaddrinfo failed before any HTTP connection; recorded execution output confirms DNS failure before dispatch. Reserved against the local cap: USD 0.

## Rate sources

| Provider | Model | Tier | Billing unit | Price | Currency | Unit size | As of | Source |
|---|---|---|---|---:|---|---:|---|---|
| typesafe | jev | standard | input_tokens | 0.042 | USD | 1000000 | 2026-10-20 | https://docs.typesafe.ai/models |
| typesafe | jev | standard | output_tokens | 0 | USD | 1000000 | 2026-10-20 | https://docs.typesafe.ai/models |
| typesafe | jev-latest | standard | input_tokens | 0.042 | USD | 1000000 | 2026-10-20 | https://docs.typesafe.ai/models |
| typesafe | jev-latest | standard | output_tokens | 0 | USD | 1000000 | 2026-10-20 | https://docs.typesafe.ai/models |

## Measured runs

| Run | Phase | Input rows | Input SHA-256 | Pilot IDs | Completed | Failed | Unique texts | Cache hits | Workers | Wall seconds | Throughput (inputs/sec) | Cost per 1,000 inputs | Cost per completed record | Local compute |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| cold-100-20261020T183808Z | cold | 100 | c884ac3b9be5066995d5063f96ad9af6e5e082975788c1684c4f6b6ea661dd0e | 100 | 0 | 100 | 100 | 0 | 1 | 0.242452 | 412.45 | unavailable | unavailable | unknown/not recorded |
| cold-100-20261020T184234Z | cold | 100 | c884ac3b9be5066995d5063f96ad9af6e5e082975788c1684c4f6b6ea661dd0e | 100 | 100 | 0 | 100 | 0 | 1 | 0.30301 | 330.02 | unavailable | unavailable | unknown/not recorded |
| warm-100-20261020T184300Z | warm | 100 | c884ac3b9be5066995d5063f96ad9af6e5e082975788c1684c4f6b6ea661dd0e | 100 | 100 | 0 | 100 | 100 | 1 | 0.000749 | 133511.35 | unavailable | unavailable | unknown/not recorded |
| cold-500-20261020T185608Z | cold | 500 | a94e31663ee7b7eaa77e23b7a8425b530cc0c866ed5e714953172a0afef6a12f | 500 | 500 | 0 | 479 | 121 | 1 | 50.222894 | 9.96 | USD 0.033864 | USD 0.000034 | unknown/not recorded |
| warm-500-20261020T185705Z | warm | 500 | a94e31663ee7b7eaa77e23b7a8425b530cc0c866ed5e714953172a0afef6a12f | 500 | 500 | 0 | 479 | 500 | 1 | 0.003578 | 139742.87 | unavailable | unavailable | unknown/not recorded |
| cold-10000-20261020T191621Z | cold | 10000 | eaa62ca6d44d717302904a9c922e99b0b4584d174309cb45295ecbc2ba2a91b5 | 10000 | 1437 | 8563 | 8448 | 2031 | 1 | 0.820692 | 12184.84 | unavailable | unavailable | unknown/not recorded |
| cold-10000-20261020T191948Z | cold | 10000 | eaa62ca6d44d717302904a9c922e99b0b4584d174309cb45295ecbc2ba2a91b5 | 10000 | 1437 | 8563 | 8448 | 2031 | 1 | 0.845103 | 11832.88 | unavailable | unavailable | unknown/not recorded |
| cold-10000-20261020T192125Z | cold | 10000 | eaa62ca6d44d717302904a9c922e99b0b4584d174309cb45295ecbc2ba2a91b5 | 10000 | 2741 | 7259 | 8448 | 2031 | 1 | 211.452189 | 47.29 | USD 0.004221 | USD 0.000015 | unknown/not recorded |
| cold-10000-20261020T192530Z | cold | 10000 | eaa62ca6d44d717302904a9c922e99b0b4584d174309cb45295ecbc2ba2a91b5 | 10000 | 10000 | 0 | 8448 | 3018 | 1 | 2247.152364 | 4.45 | USD 0.031420 | USD 0.000031 | unknown/not recorded |
| warm-10000-20261020T200310Z | warm | 10000 | eaa62ca6d44d717302904a9c922e99b0b4584d174309cb45295ecbc2ba2a91b5 | 10000 | 10000 | 0 | 8448 | 10000 | 1 | 0.037043 | 269956.54 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 26640 | 73360 | 78099 | 30349 | 2 | 7.52051 | 13296.97 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 31283 | 68717 | 78099 | 30349 | 2 | 320.264755 | 312.24 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 55267 | 44733 | 78099 | 34153 | 2 | 1562.705435 | 63.99 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 71520 | 28480 | 78099 | 55987 | 2 | 967.448756 | 103.36 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 77750 | 22250 | 78099 | 71768 | 2 | 388.972316 | 257.09 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 83508 | 16492 | 78099 | 77899 | 2 | 380.724036 | 262.66 | unavailable | unavailable | unknown/not recorded |
| cold-100000-20261020T213754Z | cold | 100000 | cf2641e8f3075e392a4c693c7cd45484c68e907569c48718cf131f0e321d643c | 100000 | 100000 | 0 | 78099 | 83586 | 2 | 1764.81076 | 56.66 | unavailable | unavailable | unknown/not recorded |
| dashboard-finalization-100000 | finalization | 0 | fb050d3779f676c15854b81d18d5e1e611d13291adfb10953c1a0564b6604be3 | 0 | 0 | 0 | 0 | 0 | 1 | 0.521404 | 0.00 | unavailable | unavailable | unknown/not recorded |
| cold-custom-f5a801c0b3b7-20261021T014956Z | cold | 30 | f5a801c0b3b74666bccc823e964a12f9b79b78c7f9625237648e3beb7d77d5c4 | 30 | 30 | 0 | 30 | 0 | 2 | 19.036084 | 1.58 | USD 0.053911 | USD 0.000054 | unknown/not recorded |
| cold-custom-0736cdcd005a-20261021T015103Z | cold | 30 | 0736cdcd005add04a7ff7de9853c0c29faa0f19dea4fd75e873dcccda6d1ddb4 | 30 | 30 | 0 | 30 | 4 | 2 | 5.541814 | 5.41 | USD 0.053910 | USD 0.000054 | unknown/not recorded |
| cold-custom-2e1f03ced275-20261021T020307Z | cold | 30 | 2e1f03ced275738faea40bee2379dc77d597f0d349b0172a2814c962bf96ff22 | 30 | 30 | 0 | 30 | 4 | 2 | 6.770184 | 4.43 | USD 0.053904 | USD 0.000054 | unknown/not recorded |
| cold-custom-c884ac3b9be5-20261021T022408Z | cold | 100 | c884ac3b9be5066995d5063f96ad9af6e5e082975788c1684c4f6b6ea661dd0e | 100 | 100 | 0 | 100 | 0 | 1 | 12.779673 | 7.82 | USD 0.054427 | USD 0.000054 | unknown/not recorded |
| warm-custom-c884ac3b9be5-20261021T022426Z | warm | 100 | c884ac3b9be5066995d5063f96ad9af6e5e082975788c1684c4f6b6ea661dd0e | 100 | 100 | 0 | 100 | 100 | 1 | 0.000507 | 197238.66 | unavailable | unavailable | unknown/not recorded |

Costs are phase totals across logged model roles. Request-duration sums are not substituted for wall-clock time. Local compute is reported separately and remains unknown unless measured or estimated in the run log.

## Cold call evidence without a matching timing record

These API calls are priced from their saved token usage, but the run ledger has no matching run ID. Cost per 1,000 IDs is based on distinct review IDs in enrichment calls. Wall time is **not recorded** and is not inferred from request durations.

| Call run ID | Request attempts | Unique enrichment IDs | Successful enrichment IDs | Known API cost | Cost per 1,000 enriched IDs | Cold wall time | Usage status |
|---|---:|---:|---:|---|---|---|---|
| batch-benchmark-golden50 | 1 | 5 | 0 | unavailable | unavailable | not recorded | partial or unresolved |
| batch-benchmark-golden50-w1 | 10 | 50 | 50 | USD 0.002229 | USD 0.044586 | not recorded | priced usage |
| batch-benchmark-golden50-w2 | 10 | 50 | 50 | USD 0.002229 | USD 0.044586 | not recorded | priced usage |
| cold-100-20261020T184149Z | 110 | 100 | 100 | USD 0.004468 | USD 0.044684 | not recorded | priced usage |
| worker-comparison-golden50-w1 | 50 | 50 | 50 | USD 0.002135 | USD 0.042693 | not recorded | priced usage |
| worker-comparison-golden50-w2 | 50 | 50 | 50 | USD 0.002135 | USD 0.042693 | not recorded | priced usage |

## Projection readiness

Target counts from the editable projection file: source_rows=660622, nonempty_reviews=660609, empty_text_quarantines=13, distinct_nonempty_texts=484189.
Spend budget: USD 8.0.
Observed cold work units by role: enrich_primary=78489, enrich_fallback=0, verify=7829, group=0, memo=0.
Only calls with complete token usage are used to calibrate per-work-unit cost. Failed calls with missing usage remain listed as unresolved and are excluded from calibration. Request counts are recorded as operational metadata, not priced as token usage.

| Scenario | API projection | Estimated wall time | Budget check | Status |
|---|---|---|---|---|
| 10k_forecast_from_500 | USD 0.357042 | 1036.97 sec | within budget | complete projection |
| full_base | USD 21.693441 | 63003.52 sec | OVER BUDGET | complete projection |
| final_100000_at_10k_unique_rate | USD 3.785013 | 10992.68 sec | within budget | complete projection |
| final_100000_at_population_unique_rate | USD 3.282826 | 9534.44 sec | within budget | complete projection |
| final_100000_no_reuse | USD 4.480366 | 13012.17 sec | within budget | complete projection |
| full_no_reuse_comparison | USD 29.597703 | 85959.59 sec | OVER BUDGET | complete projection |

Projection cost uses per-stage charges per logical work unit from cold calls, including retries logged under each operation. Runtime uses recorded stage wall times and does not assume unmeasured concurrency speedups.


## Controls

- Maximum workers: 2
- Maximum output tokens: not set
- Fallback fraction cap: 0.0
- No paid API calls were made by this report.

