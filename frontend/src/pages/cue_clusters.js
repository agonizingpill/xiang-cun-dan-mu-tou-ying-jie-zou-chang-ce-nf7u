        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "节奏相近的对场 cue",
  "module": "对场节奏簇",
  "caption": "对场节奏簇",
  "detail": "DTW 比较长短不同的拍点序列，然后按预计算距离做凝聚层次分类。",
  "path": "/cue_clusters",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "track",
      "label": "输入素材"
    },
    {
      "name": "representative",
      "label": "簇样板"
    },
    {
      "name": "status",
      "label": "合用状态"
    },
    {
      "name": "distance",
      "label": "DTW 距离"
    },
    {
      "name": "members",
      "label": "簇内轨迹"
    },
    {
      "name": "token",
      "label": "计算凭据"
    }
  ],
  "layout": "split",
  "view": "grid",
  "actions": [
    {
      "name": "disable_track",
      "label": "停用见证素材",
      "buttonLabel": "停用",
      "path": "/cue_clusters/disable-track",
      "fields": [
        {
          "name": "track",
          "label": "见证素材编号",
          "kind": "text",
          "initial": "CUE-03"
        }
      ],
      "help": "新比较排除该素材；以它为样板的待签结果不予签认，已签簇停止合用，并撤销未开播回单。",
      "roles": [
        "reviewer"
      ],
      "success": "已停用，关联未开播回单已撤销"
    },
    {
      "name": "compare_cues",
      "label": "计算可迁移节奏簇",
      "path": "/cue_clusters/compare-cues",
      "fields": [
        {
          "name": "track",
          "label": "试投素材",
          "kind": "text",
          "initial": "CUE-FINAL"
        }
      ],
      "help": "返回最近代表 cue 与簇内成员。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "save_cluster",
      "label": "保留对场节奏凭据",
      "path": "/cue_clusters/save-cluster",
      "fields": [
        {
          "name": "code",
          "label": "节奏簇编号",
          "kind": "text",
          "initial": "BEAT-24"
        },
        {
          "name": "token",
          "label": "任务",
          "kind": "token",
          "initial": ""
        }
      ],
      "help": "输出供放映领班查阅的代表节奏。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "cue_clusters";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
