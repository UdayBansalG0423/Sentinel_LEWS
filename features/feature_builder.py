def build_features(fused_data):
    X = []
    for i in range(len(fused_data)):
        X.append([fused_data.iloc[i,1]])
    return X
