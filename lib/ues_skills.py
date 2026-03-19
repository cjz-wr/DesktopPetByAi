import logging
import lib.LogManager as LogManager
from plugins_manage import PluginManager

class UESkills:
    def __init__(self, skill_info):
        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)
        self.skill_info = skill_info
        self.skill_parameter_ls = None
        self.skills_ls = self.load_skills()

    def load_skills(self):
        import json
        with open("yyskills/skill_list.json", 'r', encoding='utf-8') as f:
            return json.load(f)

    
    def analyze_skill(self):
        skill_ls = self.skill_info.split(":")
        self.skill_name  = skill_ls[0] #技能名
        self.skill_parameter = skill_ls[1] #技能参数（如果有的话）

        #处理多个参数的情况
        if "," in self.skill_parameter:
            self.skill_parameter_ls = self.skill_parameter.split(",")


        #用于处理有外部插件的情况
        if self.skills_ls[self.skill_name]["have_plugin"]:
            #处理不需要传入参数的情况
            if self.skill_name == self.skill_parameter and self.skill_parameter_ls is None:
                self.logger.debug(f"技能 {self.skill_name} 需要调用外部插件")
                plugins = PluginManager.load_plugins()
                plugin_result = PluginManager.call_plugin(plugins, self.skill_name)
                return plugin_result
            
            #处理需要传入参数的情况
            self.logger.debug(f"有参数的技能{self.skill_name}执行")
            plugins = PluginManager.load_plugins()
            plugin_result = PluginManager.call_plugin(plugins, self.skill_name, *self.skill_parameter_ls)
            return plugin_result
        
        if self.skills_ls[self.skill_name]["detailed_info"]:
            with open(f"yyskills/{self.skill_name}.md", "r", encoding='utf-8') as f:
                detailed_info = f.read()
            return detailed_info
        else:
            self.logger.error(f"调用技能时出现未预料到的结果: {self.skill_info}")
            
    
    def get_skill_info(self, skill_name):
        return self.skills.get(skill_name, None)
    

    def run_skill(self):
        pass