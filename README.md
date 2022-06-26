# SbsRsSimulator

## _controller/ - 입출고 할당 알고리즘 모음
* storage_basic.py
* retrieval_basic.py
 
## _env/ - 환경 Object 모음
* _objecy.py : Object들의 Base Class 모음
* _msc.py : 설비들의 Class 모음
* _static.py : 정적 설비 Class 모음
* _dynamic.py : 동적 설비 Class 모음
* _env.py : 환경 구축
 
## _model/ : DQN Agent 관리 파일
* _agent/ : agent network 저장폴더
* _agent.py

## Root
* _viewer.py : 환경 시각화 도구 (pygame)
* _util.py : 프로그램 도구 모음
* _simulator.py : 통합환경
* _getData.py : 환경에서 State를 추출
* main.py : 실행파일
