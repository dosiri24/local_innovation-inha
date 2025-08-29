def generate_simple_walking_route(start, end, distance_m):
    """간단하고 자연스러운 도보 경로 생성"""
    import math
    
    print(f"[간단 도보] 거리: {distance_m}m")
    
    start_lat = float(start['lat'])
    start_lng = float(start['lng'])
    end_lat = float(end['lat'])
    end_lng = float(end['lng'])
    
    # 시작점과 끝점
    path_points = [{'lat': start_lat, 'lng': start_lng}]
    
    # 거리에 따라 중간점 개수 결정
    if distance_m < 200:
        waypoints = []  # 매우 짧은 거리는 직선
    elif distance_m < 800:
        waypoints = [0.33, 0.67]  # 2개 중간점
    elif distance_m < 2000:
        waypoints = [0.25, 0.5, 0.75]  # 3개 중간점
    else:
        waypoints = [0.2, 0.4, 0.6, 0.8]  # 4개 중간점
    
    # 중간점들 생성 (부드러운 곡선)
    for progress in waypoints:
        # 기본 직선상의 점
        mid_lat = start_lat + (end_lat - start_lat) * progress
        mid_lng = start_lng + (end_lng - start_lng) * progress
        
        # 자연스러운 곡선 오프셋 (매우 작게)
        curve_offset = math.sin(progress * math.pi) * distance_m * 0.000002
        
        path_points.append({
            'lat': mid_lat + curve_offset,
            'lng': mid_lng + curve_offset * 0.5
        })
    
    # 끝점
    path_points.append({'lat': end_lat, 'lng': end_lng})
    
    print(f"[간단 도보] 생성된 점 수: {len(path_points)}")
    return path_points
