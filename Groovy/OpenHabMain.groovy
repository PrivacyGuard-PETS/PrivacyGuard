import groovy.console.ui.AstNodeToScriptAdapter
import groovy.console.ui.ScriptToTreeNodeAdapter
import groovy.console.ui.SwingTreeNodeMaker
import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import org.codehaus.groovy.control.CompilerConfiguration

import javax.swing.tree.DefaultMutableTreeNode

class OpenHabMain {

    static int phaseInt = 3 //CONVERSION
    static SwingTreeNodeMaker swingTreeNodeMaker = new SwingTreeNodeMaker()
    static GroovyClassLoader groovyClassLoader = new GroovyClassLoader()
    static CompilerConfiguration compilerConfig = null
    static boolean showScriptFreeFormBool = true
    static boolean showScriptClassBool = false
    static boolean showClosureClassesBool = false
    static ScriptToTreeNodeAdapter scriptToTreeNodeAdapter = new ScriptToTreeNodeAdapter(groovyClassLoader, showScriptFreeFormBool, showScriptClassBool, showClosureClassesBool, swingTreeNodeMaker, compilerConfig)

    static String projectRootStr = "."
    // static String projectResultsStr = "${projectRootStr}/Files/Datasets"
   static String projectResultsStr = "${projectRootStr}/Files/Examples"
    static String datasetDirStr = "${projectRootStr}/Files/Temporary"

    static void main(String[] args) {

        if(args.size()>0 && args[0]=="Datasets"){
            projectResultsStr = "${projectRootStr}/Files/Datasets"
        }

        FileWriter fileWriter = new FileWriter("${projectResultsStr}/OpenHAB.json")
        BufferedWriter bufferedWriter = new BufferedWriter(fileWriter)

        long beginTimeLong = System.currentTimeMillis()
        bufferedWriter.write("{\n")

        JsonSlurper jsonSlurper = new JsonSlurper()

        Map openHabDataset = jsonSlurper.parse(new File("${datasetDirStr}/OpenHAB.json"))
        int numRulesInt = openHabDataset.size()

        // println(numRulesInt)

        int iInt = 0

        for (itemEntry in openHabDataset) {
            String filenameStr = itemEntry.key
            String descriptionStr = itemEntry.value["descriptionStr"]
            Map inputMap = itemEntry.value["inputMap"]
            List triggersList = itemEntry.value["triggersList"]
            String ruleStr = itemEntry.value["ruleStr"]

//            print(filenameStr)
//            print(ruleStr)

            try {

                DefaultMutableTreeNode rootDmtn = scriptToTreeNodeAdapter.compile(ruleStr, phaseInt)
                OpenHabHelper openHabHelper = new OpenHabHelper(rootDmtn, filenameStr, descriptionStr, inputMap, triggersList)
                rootDmtn.getFirstChild().getPropertyValue("text")

                Map InformationMap = openHabHelper.getInformation()
//                Map InformationMap = [:]

                String InformationJsonStr = JsonOutput.toJson(InformationMap)
                String InformationPrettyJsonStr = JsonOutput.prettyPrint(InformationJsonStr)
                bufferedWriter.write("\"${filenameStr}\":")
                bufferedWriter.write(InformationPrettyJsonStr)
                if (iInt == numRulesInt - 1) {
                    bufferedWriter.write("\n")
                } else {
                    bufferedWriter.write(",\n")
                }
                bufferedWriter.flush()
            }
            catch (Exception e) {
                // println("Exception -> ${filenameStr}")
//                File newFile = new File("${exceptionAppDirStr}/${fileNameStr}")
//                newFile << appFile.text
            }
            iInt += 1
        }

        bufferedWriter.write("}\n")
        bufferedWriter.close()

        long endTimeLong = System.currentTimeMillis()
        long totalSecsLong = (endTimeLong - beginTimeLong) / 1000

        long hoursLong = totalSecsLong / 3600;
        long minutesLong = (totalSecsLong % 3600) / 60;
        long secondsLong = totalSecsLong % 60;

        // println("Time cost: ${hoursLong} Hours, ${minutesLong} Minutes, ${secondsLong} Seconds.")
    }
}
