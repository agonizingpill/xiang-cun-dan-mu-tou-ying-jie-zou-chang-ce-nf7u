        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "对场合用与分路提示",
  "module": "交场分路回单",
  "caption": "交场分路回单",
  "detail": "同协议的签验场地可合用。异协议要留下一条本场分路提醒。",
  "path": "/cue_routing",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "cluster",
      "label": "节奏簇"
    },
    {
      "name": "destination",
      "label": "目标场地"
    },
    {
      "name": "route",
      "label": "物理分路"
    },
    {
      "name": "status",
      "label": "交场状态"
    },
    {
      "name": "air_status",
      "label": "开播状态"
    },
    {
      "name": "line_status",
      "label": "分路占线"
    }
  ],
  "layout": "flip",
  "view": "stack",
  "actions": [
    {
      "name": "confirm_on_air",
      "label": "交场确认开播",
      "buttonLabel": "确认开播",
      "path": "/cue_routing/confirm-on-air",
      "fields": [
        {
          "name": "code",
          "label": "交场回单编号",
          "kind": "text",
          "initial": "ROUTE-0"
        }
      ],
      "help": "值守在交场确认开播。已开播回单会保留并继续占线；与停用同时提交时，先落定者生效。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已确认开播"
    },
    {
      "name": "share_cue",
      "label": "签回跨场合用",
      "path": "/cue_routing/share-cue",
      "fields": [
        {
          "name": "code",
          "label": "分路回单",
          "kind": "text",
          "initial": "ROUTE-24"
        },
        {
          "name": "cluster",
          "label": "节奏簇",
          "kind": "text",
          "initial": "BEAT-24"
        },
        {
          "name": "destination",
          "label": "目的场地",
          "kind": "text",
          "initial": "HALL-C"
        },
        {
          "name": "route",
          "label": "分路",
          "kind": "text",
          "initial": "C-1"
        }
      ],
      "help": "签认前核对不同场地的计量协议。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "record_separate",
      "label": "记录异协议分路提示",
      "path": "/cue_routing/record-separate",
      "fields": [
        {
          "name": "code",
          "label": "提醒编号",
          "kind": "text",
          "initial": "ROUTE-25"
        },
        {
          "name": "cluster",
          "label": "节奏簇",
          "kind": "text",
          "initial": "BEAT-24"
        },
        {
          "name": "destination",
          "label": "目的场地",
          "kind": "text",
          "initial": "HALL-B"
        },
        {
          "name": "route",
          "label": "本地替代分路",
          "kind": "text",
          "initial": "B-2"
        }
      ],
      "help": "保存本场分路编号给当地值守。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "cue_routing";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
