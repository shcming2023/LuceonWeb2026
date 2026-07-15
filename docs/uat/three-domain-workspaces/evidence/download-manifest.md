# 浏览器下载证据清单

验证日期：2026-07-15（Asia/Shanghai）

验证入口：隔离 clean-image UAT 栈 `http://127.0.0.1:38081`

所有文件均由登录后的真实浏览器页面点击下载，不是由命令行复制 MinIO 对象。下载后使用本机 `shasum -a 256` 复核。

| 资产 | 材料 | 受控身份 | 下载字节数 | SHA-256 |
|---|---|---|---:|---|
| 源 PDF | `2025.pdf` | `material_pk=1335`, `material_id=pdf-642599641f3b15e1` | 175841 | `642599641f3b15e11b19f383379864081464be1f9c79bdd4f1e9334489c4b1ad` |
| MinerU 冻结归档 | `2025.pdf` | 资产目录返回的 MinerU artifact ID | 369548 | `88a6c11b66f90920e47dc067b7ff28bc51e8f347942978b54bda5164eb152ab7` |
| Popo 冻结归档 | `2025.pdf` | 资产目录返回的 Popo artifact ID | 401261 | `5d2aa644a44a75bde86d1dce0197ef2a2a81cd1a1de9b046596e6213a45297fe` |
| 已接受 LaTeX ZIP | `2025.pdf` | `output_id=554` | 613615 | `481c03a9a2a04cf118eb10a7d2e3086ca1bcb9a63928132cdd9057f7f32c96bc` |
| 已接受编译 PDF | `2025.pdf` | `output_id=554` | 779763 | `8ccf5e4e2e54202861e13942fa2c0e8e40989f51c10f13537a6b674ef2bd30a6` |
| 大型 MinerU 冻结归档 | `material_pk=1337` | 资产目录返回的 MinerU artifact ID | 120118467 | `302da19585db2a61005c0e08b339be9d09b3884bfb2de6ab8b409ba419e037de` |

已接受 LaTeX ZIP 解压后的顶层内容为：

- `images/`
- `figure/`
- `main.tex`
- `elegantbook.cls`

其中固定 figure 资产为 `figure/cover.jpg` 和 `figure/logo.jpg`。

大型归档下载前后，后端容器内存约从 117.2 MiB 增至 119.3 MiB，容器 restart 为 0、OOMKilled 为 false。通过前端反向代理请求单字节 Range 得到 `206` 和 `Content-Range: bytes 0-0/369548`，证明下载链路采用流式响应并支持 HTTP Range。

未将上述下载文件提交到 Git；仓库只保留文件身份、长度、哈希和浏览器截图，避免复制受保护教材资产。
