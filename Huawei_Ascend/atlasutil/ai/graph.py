import hiai
from hiai.nn_tensor_lib import DataType
import numpy as np
import copy
import  os
import random

class Graph():
    def __init__(self, model_path):
        self.model_path = model_path
        self.graph = self.CreateGraph()

    def CreateGraph(self):
        '''
        Create graph

        Returns:
            graph
        '''
        path, filename =  os.path.split(self.model_path)
        nntensorlist_object =hiai.NNTensorList()
        id = random.randint(1, 2**32-1)
        graph = hiai.Graph(hiai.GraphConfig(graph_id=id))
        print("id:",id)
        with graph.as_default():
            engine = hiai.Engine()
            ai_model_desc = hiai.AIModelDescription(name = filename, path = self.model_path)
            ai_config = hiai.AIConfig(hiai.AIConfigItem("Inference", "item_value_2"))
            final_result = engine.inference(input_tensor_list=nntensorlist_object,
                                        ai_model=ai_model_desc,
                                        ai_config=ai_config)
        ret = copy.deepcopy(graph.create_graph())
        if ret != hiai.HiaiPythonStatust.HIAI_PYTHON_OK:
            graph.destroy()
            raise Exception("create graph failed, ret ", ret)
        print("create graph successful")
        return graph

    def create_graph_with_dvpp(self, resize_cfg):
        '''
        Create graph with dvpp

        Args:
            resize_cfg: resize parameter, (resize_w, resize_h)
                resize_w: width of the destination resolution
                resize_h: height of the destination resolution
            
        Returns:
            graph: a graph configured with dvpp

        Raises:
            Exception("[create_graph_with_dvpp]: create graph failed, ret ", ret)
        '''
        nntensorlist_object =hiai.NNTensorList()
        id = random.randint(1, 2**32-1)
        graph = hiai.Graph(hiai.GraphConfig(graph_id=id))
        print("id:",id)
        with graph.as_default(): 
            engine = hiai.Engine()
            resize_config = hiai.ResizeConfig(resize_width=resize_cfg[0], resize_height = resize_cfg[1])
            nntensorlist_object = engine.resize(input_tensor_list=nntensorlist_object, config=resize_config)
            ai_model_desc = hiai.AIModelDescription(name=os.path.basename(self.model_path), path=self.model_path)
            ai_config = hiai.AIConfig(hiai.AIConfigItem("Inference", "item_value_2"))
            final_result = engine.inference(input_tensor_list=nntensorlist_object,
                                        ai_model=ai_model_desc,
                                        ai_config=ai_config)
        ret = copy.deepcopy(graph.create_graph())
        if ret != hiai.HiaiPythonStatust.HIAI_PYTHON_OK:
            graph.destroy()
            raise Exception("[create_graph_with_dvpp]: create graph failed, ret ", ret) 
        print("[create_graph_with_dvpp]: create graph successful")
        return graph

    def Inference(self, input_data):
        '''
        Inferece interface, process data with configured model

        Args:
            input_data: a numpy array, the data user wants to process
        
        Returns:
            a list, inference result
        '''
        inputNntensorList = self.CreateNntensorList(input_data)
        return self.graph.proc(inputNntensorList)

    def CreateNntensorList(self, input_data):
        '''
        Create NNTensorList instance with input_data

        Args:
            input_data: a numpy array, the data user wants to process

        Returns:
            nntensorList: NNTensorList instance that can be used by graph.proc
        '''
        inputImageTensor = hiai.NNTensor(input_data)
        nntensorList=hiai.NNTensorList(inputImageTensor)
        return nntensorList

    def __del__(self):
        '''
        Destroy graph
        '''
        self.graph.destroy()