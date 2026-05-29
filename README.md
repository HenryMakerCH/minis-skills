# Minis Skills

用 [Minis](https://github.com/OpenMinis/OpenMinis) 做的 Skills 集合。

## Skills

| 名称 | 说明 |
|------|------|
| [x-tweet-fetcher](./x-tweet-fetcher/) | 通过 X/Twitter 内部 GraphQL API 获取指定用户最新推文。纯标准库，零依赖。 |
| [nhentai-hub](./nhentai-hub/) | 通过 nhentai API v2 搜索、浏览、下载和管理画廊。需 API Key。 |

## 使用

把目录复制到 `/var/minis/skills/<skill-name>/`，Minis 会自动加载。

```sh
# 克隆所有 skill
cd /var/minis/skills
git clone --depth 1 git@github.com:HenryMakerCH/minis-skills.git temp && \
  cp -r temp/* . && rm -rf temp
```
