# PipelineRoute views
class PipelineRouteListCreateView(generics.ListCreateAPIView):
    queryset = PipelineRoute.objects.all()
    serializer_class = PipelineRouteSerializer

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
        else:
            serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PipelineRouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PipelineRoute.objects.all()
    serializer_class = PipelineRouteSerializer

# PipelineFault views
class PipelineFaultListCreateView(generics.ListCreateAPIView):
    queryset = PipelineFault.objects.all()
    serializer_class = PipelineFaultSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class PipelineFaultDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PipelineFault.objects.all()
    serializer_class = PipelineFaultSerializer
