import groovy.console.ui.ScriptToTreeNodeAdapter
import groovy.console.ui.SwingTreeNodeMaker
import groovy.json.JsonOutput
import org.codehaus.groovy.control.CompilerConfiguration

import javax.swing.tree.DefaultMutableTreeNode

class SmartThingsMain {
    static int phaseInt = 3 //CONVERSION
    static SwingTreeNodeMaker swingTreeNodeMaker = new SwingTreeNodeMaker()
    static GroovyClassLoader groovyClassLoader = new GroovyClassLoader()
    static CompilerConfiguration compilerConfig = null
    static boolean showScriptFreeFormBool = true
    static boolean showScriptClassBool = false
    static boolean showClosureClassesBool = false
    static ScriptToTreeNodeAdapter scriptToTreeNodeAdapter = new ScriptToTreeNodeAdapter(groovyClassLoader, showScriptFreeFormBool, showScriptClassBool, showClosureClassesBool, swingTreeNodeMaker, compilerConfig)

    static String projectRootStr = "."
    static String projectResultsStr = "${projectRootStr}/Files/Examples"
//    static String projectResultsStr = "${projectRootStr}/Files/Datasets"
    static String projectFilesStr = "${projectRootStr}/Files/Reference"
    static String datasetDirStr = "${projectRootStr}/Examples/SmartThings"
//    static String datasetDirStr = "${projectRootStr}/Datasets/SmartThings"

//    static String exceptionAppDirStr = "${projectRootStr}/Files/Exception"


    static void main(String[] args) throws IOException {

        if(args.size()>0 && args[0]=="Datasets"){
            projectResultsStr = "${projectRootStr}/Files/Datasets"
            datasetDirStr = "${projectRootStr}/Datasets/SmartThings"
        }

        String resultInformationFileStr = "${projectResultsStr}/SmartThings.json"

        List<File> filesList = new File(datasetDirStr).listFiles().sort { it.name }
        int numFilesInt = filesList.size()

        FileWriter fileWriter = new FileWriter(resultInformationFileStr)
        BufferedWriter bufferedWriter = new BufferedWriter(fileWriter)

        long beginTimeLong = System.currentTimeMillis()

        bufferedWriter.write("{\n")

        for (int iInt = 0; iInt < numFilesInt; iInt++) {
            File appFile = filesList[iInt]
            String fileNameStr = appFile.getName()

//            if(fileNameStr!="ecobeeChangeMode[natalan@SmartThings].groovy"){
//                continue
//            }

            // println("${iInt}. ${fileNameStr}")

            try {
                DefaultMutableTreeNode rootDmtn = scriptToTreeNodeAdapter.compile(appFile.text, phaseInt)
                SmartThingsHelper smartThingsHelper = new SmartThingsHelper(rootDmtn)
                rootDmtn.getFirstChild().getPropertyValue("text")

                Map InformationMap = smartThingsHelper.getInformation()

                String InformationJsonStr = JsonOutput.toJson(InformationMap)
                String InformationPrettyJsonStr = JsonOutput.prettyPrint(InformationJsonStr)
                bufferedWriter.write("\"${fileNameStr}\":")
                bufferedWriter.write(InformationPrettyJsonStr)
                if (iInt == numFilesInt - 1) {
                    bufferedWriter.write("\n")
                } else {
                    bufferedWriter.write(",\n")
                }
                bufferedWriter.flush()
            }
            catch (Exception e) {
                // println("Exception -> ${fileNameStr}")
//                File newFile = new File("${exceptionAppDirStr}/${fileNameStr}")
//                newFile << appFile.text
            }

//            break
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
