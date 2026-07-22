# 빌드 메모

이 저장소의 도구는 원본 Steam Windows판 Big Dipper 파일을 입력으로 사용합니다. 원본 파일 자체는 저장소에 포함하지 않습니다.

## 주요 산출물

- `BigDipperKoreanSafe.dll`: 런타임 UI·이름 변환 플러그인
- `resources.assets`: 영어 원문 기반 한국어 `Text3`가 적용된 자산
- `sharedassets1.assets`: Noto Sans CJK KR Medium 기반 TMP SDF 폰트가 적용된 자산

## 검증 순서

1. 원본 게임 실행 파일과 `Assembly-CSharp.dll`의 빌드 해시를 확인합니다.
2. 최종 번역 맵과 `Text3_Korean.txt`의 SHA-256을 확인합니다.
3. `build_tmp_korean_font.py`로 번역, 플러그인 출력, 원본 CJK glyph의 합집합을 빌드합니다.
4. `finalize_package.py`로 manifest와 배포 파일 해시를 고정합니다.
5. `build_release_zip_1_2_2.py`로 재현 가능한 ZIP을 생성합니다.
6. `audit_release_1_2_2.py`로 패키지, ZIP, 설치본을 교차 검사합니다.

도구에는 이 작업 환경의 경로가 포함돼 있으므로 다른 환경에서 사용할 때는 상단의 경로 상수를 먼저 조정해야 합니다.
