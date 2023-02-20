## START EDITABLE BLOCK
## Change the values for $filepath, $outfile to match your folder structure
## Change the value for $token to match the supplied token for APC_DISCHARGE

$filepath= "\\server\share\NHSEFDF\DATA_OUT\FDF_APC_DISCHARGE_v1_0.csv"
$outfile = "\\server\share\NHSEFDF\DATA_IN\FDF_API_RESPONSE\FDF_APC_DISCHARGE_v1_0_"
$token = "SECURITY_TOKEN"

## END EDITABLE BLOCK

$Error.Clear()
$outfiletimestamp = Get-Date -Format FileDateTime
$filename= [System.IO.Path]::GetFileNameWithoutExtension($filepath)
$headers = @{"Authorization"= "Bearer " + $token}
$body = (Get-Content -path $filepath) -join "`n"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

  $response =  try
    {Invoke-WebRequest -Method POST -Headers $headers -ContentType "application/octet-stream" -uri ("https://agemdscro.palantirfoundry.co.uk/secure-upload/api/blobs/csv?fileName=" + $filename) -Body $body}
    catch
    { 
    #$_.Exception.Response
    $Error
    }

   If ($Error) {
       Write-Host ("`tResponse: ERROR")
       Write-Host ("`tResponseUri: " + $response.Exception.Response.ResponseUri)
       Write-Host ("`tStatusCode: " + $response.Exception.Response.StatusCode)
       Write-Host ("`tStatusDescription: " + $response.Exception.Response.StatusDescription)
       Write-Host ("`tMessage: " + $response.Exception.Message)     
       Write-Host ("`tMessageDetail: " + $response.ErrorDetails) 

       $outfile = $outfile + $outfiletimestamp + "_ERROR.txt"

       Out-File $outfile -InputObject $response.Exception.Response 
       Out-File $outfile -InputObject $response.Exception.Message -Append
       add-content -value $response.ErrorDetails -Path $outfile
  }
   Else {
       Write-Host ("`tResponse: SUCCESS")
       Write-Host ("`tResponseUri: " + $response.PSObject.BaseObject.BaseResponse.ResponseUri) 
       Write-Host ("`tStatusCode: " + $response.StatusCode)
       Write-Host ("`tStatusDescription: " + $response.StatusDescription)  
       Write-Host ("`tMessage: " + $response.StatusDescription)     
       Write-Host ("`tMessageDetail: " + $response.StatusDescription)

       $outfile = $outfile + $outfiletimestamp + "_SUCCESS.txt"

       Out-File $outfile -InputObject $response
       
   }
  
   
  

 
       





