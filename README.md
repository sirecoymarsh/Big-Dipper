# Big Dipper 비공식 한국어 패치

Steam Windows판 **Big Dipper**용 비공식 한국어 패치입니다.

- 최신 버전: **1.2.2**
- 번역 기준: 영어 원문
- 한국어 출력 슬롯: Simplified Chinese (`Text3`)
- 번역 레코드: 1,408개
- 보존한 스크립트 명령: 579개
- 폰트: Noto Sans CJK KR Medium 기반 TextMeshPro SDF, 2,769 glyph

## 설치

1. Releases에서 `BigDipper_Korean_Patch_1.2.2.zip`을 받습니다.
2. 압축을 풉니다.
3. 게임을 완전히 종료한 상태에서 `설치.bat`을 실행합니다.
4. Steam에서 게임을 실행합니다.

기본 설치 경로는 다음과 같습니다.

```text
P:\SteamLibrary\steamapps\common\Big Dipper\WIN
```

다른 경로에 설치했다면 PowerShell에서 다음처럼 실행합니다.

```powershell
.\설치.ps1 -GameDir '다른 경로\Big Dipper\WIN'
```

제거할 때는 게임을 종료한 뒤 `제거.bat`을 실행합니다.

## 1.2.2 수정 사항

- `DialogueManager.set_outputChar`를 직접 후킹해 이름 공개 전 `소녀`, 공개 후 `줄리아`를 정확히 표시
- 실제 게임 텍스트 writer를 개별 후킹해 메뉴, 설정, 확인창을 즉시 번역
- 불러오기·덮어쓰기·삭제·메인 메뉴 확인문과 버튼 번역
- 씬에 러시아어로 직렬화돼 있던 메뉴 설명을 검수된 한국어로 교체
- 위험한 대형 난독화 메서드 후킹을 제거하고 훅별 실패 격리 적용
- 한글과 기존 CJK glyph를 함께 보존하는 Noto Sans CJK KR Medium 폰트 적용

## 검증

- 실제 게임 런타임 검사: **22/22 통과**
- 최종 패키지·ZIP·라이브 설치 교차 감사: **72/72 통과**
- 런타임 오류·경고·예외·후킹 실패: **0건**
- 번역 QA 오류·경고: **0건**

![불러오기 확인창](quality/runtime/load-confirmation.png)

![이름 공개 전](quality/runtime/julia-before-reveal.png)

![이름 공개 후](quality/runtime/julia-after-reveal.png)

## 저장소 구성

- `src/`: 런타임 한국어화 플러그인 소스
- `bin/`: 검증된 1.2.2 플러그인 DLL
- `translation/`: 최종 한국어 대본과 번역 맵
- `installer/`: 설치·복원 스크립트
- `tools/`: 폰트, 패키지, 감사 도구
- `quality/`: 번역·폰트·런타임 검증 자료
- `release/`: 릴리스 manifest와 SHA-256

전체 설치 패키지는 저장소에 직접 커밋하지 않고 GitHub Release 첨부 파일로 제공합니다.

## 릴리스 해시

`BigDipper_Korean_Patch_1.2.2.zip`

```text
00f0f456b55e587cd4fda29eebf32d5420077c2f0e6f0b7107baa898d7544da8
```

폰트 라이선스는 `licenses/OFL-NotoSansCJK.txt`를 참조하십시오.
