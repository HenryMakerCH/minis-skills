# Minis Skills

用 [Minis](https://github.com/open-minis) 做的 Skills 集合。

## Skills

| 名称 | 说明 |
|------|------|
| [x-tweet-fetcher](./x-tweet-fetcher/) | 通过 X/Twitter 内部 GraphQL API 获取指定用户最新推文。纯标准库，零依赖。 |

## 使用

把目录复制到 `/var/minis/skills/<skill-name>/`，Minis 会自动加载。

```sh
cd /var/minis/skills
git clone git@github.com:HenryMakerCH/minis-skills.git temp && \
  mv temp/x-tweet-fetcher . && rm -rf temp
```
