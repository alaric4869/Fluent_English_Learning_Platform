import { useCallback, useState } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { ListeningSentenceStatus, ListeningWorkspaceResponse } from "../types/practice";


const STATUS_LABELS: Array<[ListeningSentenceStatus, string]> = [["could_not_hear","没听清"],["difficult","困难 + 复习"],["understood","听懂"],["mastered","掌握"]];


export function ListeningPage({ resourceId }: { resourceId: number }) {
  const loader=useCallback((signal:AbortSignal)=>frontendApi.listeningWorkspace(resourceId,signal),[resourceId]); const {data,error,refresh}=useApiQuery(loader); const [hidden,setHidden]=useState(false); const [notice,setNotice]=useState("");
  async function mark(sentence:ListeningWorkspaceResponse["sentences"][number],status:ListeningSentenceStatus){try{const result=await frontendApi.markListeningSentence(resourceId,sentence.text,status);setNotice(result.review_item_id?`困难句已加入 Review · 下次 ${result.next_review_date}`:"句子状态已保存到 Notebook。");refresh();}catch(reason){setNotice(reason instanceof Error?reason.message:"保存失败");}}
  if(error)return <AppShell activePage="today"><ErrorState message={error}/></AppShell>;if(!data)return <AppShell activePage="today"><LoadingState/></AppShell>;
  return <AppShell activePage="today" plannedMinutes={data.estimated_duration_minutes}><div className="page-container listening-react-page"><header className="listening-react-header"><a className="back-link" href="/today">← 返回今日计划</a><div><div><p className="eyebrow">Intensive Listening · {data.difficulty??"level not set"}</p><h1>{data.title}</h1><p>{data.description||data.topic} · 预计 {data.estimated_duration_minutes} 分钟</p></div>{data.practice_href&&<a className="secondary-button" href={data.practice_href}>进入 IELTS 答题页</a>}</div></header>
    <section className="listening-workflow-react">{[["01","裸听一遍","不看字幕"],["02","对照文本","确认内容"],["03","标记难句","找出听不清处"],["04","逐句精听","暂停与重复"],["05","再次裸听","检查是否听懂"]].map(([n,title,sub])=><div key={n}><b>{n}</b><span>{title}<small>{sub}</small></span></div>)}</section>
    <section className="listening-media-react surface-panel"><header><div><p className="eyebrow">Real audio / video</p><h2>先播放真实材料</h2></div><span>{data.resource_type.replaceAll("_"," ")}</span></header><Media workspace={data}/></section>
    <section className="listening-transcript-react surface-panel"><header><div><p className="eyebrow">Sentence workspace</p><h2>Transcript 逐句精听</h2><p>将每句标为“没听清 / 困难 / 听懂 / 掌握”，前两项会自动进入 Review。</p></div>{data.sentences.length>0&&<button className="secondary-button" onClick={()=>setHidden(value=>!value)}>{hidden?"显示 Transcript":"隐藏 Transcript"}</button>}</header>{data.sentences.length===0?<div className="empty-state"><strong>真实音频已经可播放，但这份材料还没有 Transcript。</strong><p>{data.is_user_owned?"在资源详情中粘贴英文 Transcript 后，这里会自动拆成可标记的句子。":"内置 IELTS 真题不会伪造 Transcript；你可以进入交互答题页边听边做。"}</p></div>:<div className={`listening-sentence-list ${hidden?"transcript-hidden":""}`}>{data.sentences.map(sentence=><article key={sentence.position}><span>{String(sentence.position).padStart(2,"0")}</span><div><p>{sentence.text}</p><div>{STATUS_LABELS.map(([status,label])=><button className={sentence.status===status?"active":""} onClick={()=>mark(sentence,status)} key={status}>{label}</button>)}</div><small>{sentence.review_item_id?`已进入 Review · ${sentence.next_review_date}`:sentence.status?"已保存到 Notebook":"尚未标记"}</small></div></article>)}</div>}{notice&&<p className="practice-notice">{notice}</p>}</section>
  </div></AppShell>;
}


function Media({workspace}:{workspace:ListeningWorkspaceResponse}){if(workspace.media_kind==="youtube"&&workspace.media_url)return <div className="video-frame-react"><iframe src={workspace.media_url} title={workspace.title} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen/></div>;if(workspace.media_kind==="audio"&&workspace.media_url)return <audio className="full-audio" controls preload="metadata" src={workspace.media_url}/>;if(workspace.media_kind==="local_parts")return <div className="local-audio-list">{workspace.local_audio_parts.map(part=><div key={part.number}><span>{part.label}</span><audio controls preload="metadata" src={part.url}/></div>)}</div>;if(workspace.media_kind==="external"&&workspace.media_url)return <div className="media-fallback"><p>这个来源需要在原网站播放。</p><a className="primary-button" href={workspace.media_url} target="_blank" rel="noreferrer">打开真实材料 ↗</a></div>;return <div className="media-fallback"><p>这份资源还没有音频或视频 URL。</p><a className="secondary-button" href={`/library/${workspace.resource_id}`}>查看资源详情</a></div>;}
